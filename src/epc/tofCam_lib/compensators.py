import numpy as np
import h5py
import logging
from epc.tofCam_lib.algorithms import calc_unambiguity_distance


class OffsetCompensation():
    def __init__(self, offset, unambiguity):
        self.offset = offset
        self.unambiguity = unambiguity

    @staticmethod
    def from_file(file: str):
        with h5py.File(file, 'r') as f:
            group = f['data']
            offset = group['offset'][()]
            mod_freq = group['modulation_frequency'][()]
            unambiguity = calc_unambiguity_distance(mod_freq*1000000)
        return OffsetCompensation(offset, unambiguity)

    def compensate(self, distances):
        return (distances - self.offset) % self.unambiguity


class FourthHarmonicCompensation():
    def __init__(self, dll_step_size, lut, unambiguity):
        self.dll_step_size = dll_step_size
        self.lut = lut
        self.num_steps_calibrated = len(lut)
        self.unambiguity = unambiguity

    @staticmethod
    def from_file(file: str):
        with h5py.File(file, 'r') as f:
            group = f['data']
            lut = group['DRNU_LUT_mean'][:]
            dll_step_size = group['dll_step_size'][()]
            mod_freq = group['modulation_frequency'][()]
            unambiguity = calc_unambiguity_distance(mod_freq*1000000)
        return FourthHarmonicCompensation(dll_step_size, lut, unambiguity)

    def compensate(self, distances):
        compensatedDistances = np.zeros(distances.shape)
        for i in range(distances.shape[0]):
            for j in range(distances.shape[1]):
                index = distances[i, j] / self.dll_step_size
                if (index < 0):  # distance is outside the calibrated range -> uses the nearest available value (maybe we should not compensate or make pixel invalid)
                    compensatedDistances[i, j] = distances[i, j] - self.lut[0]
                elif (index >= self.num_steps_calibrated-1):
                    compensatedDistances[i, j] = distances[i, j] - self.lut[self.num_steps_calibrated-1]
                else:
                    lower_index = int(np.floor(index))
                    upper_index = int(np.ceil(index))
                    if lower_index == upper_index:
                        compensatedDistances[i, j] = distances[i, j] - self.lut[lower_index]
                    else:
                        lower_value = self.lut[lower_index]
                        upper_value = self.lut[upper_index]
                        interpolation_factor = index - lower_index
                        interpolated_value = lower_value + interpolation_factor * (upper_value - lower_value)
                        compensatedDistances[i, j] = distances[i, j] - interpolated_value
        compensatedDistances %= self.unambiguity
        return compensatedDistances


class DRNUCompensation():
    def __init__(self, lut: np.ndarray, step_size: float, roi=tuple[int, int, int, int]):
        self.lut = lut
        self.step_size = step_size
        self.drnu_roi = roi

    @staticmethod
    def from_file(file: str):
        with h5py.File(file, 'r') as f:
            drnu_table = f['data']
            lut = np.array(drnu_table['drnu_lut'])
            step_size = drnu_table['dll_step_size'][()]
            drnu_roi = drnu_table['roi'][()]
        return DRNUCompensation(lut, step_size, drnu_roi)

    def get_overlap_rois(self, roi1, shape1, roi2, shape2):
        # Overlap in big image coordinates
        ox0 = max(roi1[0], roi2[0])
        oy0 = max(roi1[1], roi2[1])
        ox1 = min(roi1[2], roi2[2])
        oy1 = min(roi1[3], roi2[3])

        if ox0 >= ox1 or oy0 >= oy1:
            # No overlap
            return None

        # Overlap region in local coordinates for img1
        img1_roi = (ox0 - roi1[0], oy0 - roi1[1],
                    ox1 - roi1[0], oy1 - roi1[1])
        img2_roi = (ox0 - roi2[0], oy0 - roi2[1],
                    ox1 - roi2[0], oy1 - roi2[1])

        return img1_roi, img2_roi

    def compensate(self, image: np.ndarray, cam_roi=None):
        if cam_roi is None:
            cam_roi = (0, 0, image.shape[1], image.shape[0])

        # Validate the ROI dimensions
        if (cam_roi[2] - cam_roi[0] != image.shape[1] or
                cam_roi[3] - cam_roi[1] != image.shape[0]):
            raise ValueError("ROI dimensions do not match image dimensions.")

        rois = self.get_overlap_rois(
            cam_roi, image.shape, self.drnu_roi, self.lut.shape[:2])
        if rois is None:
            logging.warning(
                "No overlap between the image and the DRNU LUT ROI. No compensation applied.")
            return image

        roi_img = rois[0]
        roi_lut = rois[1]
        lut = self.lut[roi_lut[1]:roi_lut[3], roi_lut[0]:roi_lut[2], :]

        lut_index = image[roi_img[1]:roi_img[3],
                          roi_img[0]:roi_img[2]] / self.step_size
        lut_index[lut_index > lut.shape[2]-1] -= lut.shape[2]
        floor_index = np.floor(lut_index).astype(int)
        ceil_index = np.ceil(lut_index).astype(int)
        # ceil_index[ceil_index >= lut.shape[2]]
        frac = lut_index - floor_index

        # linearly interpolate between the two closest values
        lower_error = lut[np.arange(lut.shape[0])[:, None],
                          np.arange(lut.shape[1]), floor_index]
        higher_error = lut[np.arange(lut.shape[0])[
            :, None], np.arange(lut.shape[1]), ceil_index]
        errors = higher_error * frac + lower_error * (1-frac)

        # compensate only the overlapping region
        result = image.copy()
        result[roi_img[1]:roi_img[3], roi_img[0]:roi_img[2]] -= errors
        return result


class TemperatureCompensation():
    TEMP_COEFF = 15

    def __init__(self, calib_temp, coeff=TEMP_COEFF):
        self.calibration_temperature = calib_temp
        self.temp_coeff = coeff

    @staticmethod
    def from_file(file: str):
        with h5py.File(file, 'r') as f:
            group = f['data']
            calib_temp = group['calibration_temperature'][()]
        return TemperatureCompensation(calib_temp)

    def compensate(self, distances, temperature):
        temperatureDif = temperature - self.calibration_temperature
        distances = distances - (temperatureDif * self.temp_coeff)
        return distances


class IndirectOffsetCompensation():
    def __init__(self, lut):
        self.lut = lut

    @staticmethod
    def from_file(file: str):
        pass

    def compensate(self, distance):
        pass
