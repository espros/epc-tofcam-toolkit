import numpy as np
import h5py
from door_sensor.algorithms import calc_unambiguity


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
            unambiguity = calc_unambiguity(mod_freq*1000000)
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
            unambiguity = calc_unambiguity(mod_freq*1000000)
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
    def __init__(self, lut: np.ndarray, step_size: float):
        self.lut = lut
        self.step_size = step_size

    @staticmethod
    def from_file(file: str):
        with h5py.File(file, 'r') as f:
            drnu_table = f['data']
            lut = np.array(drnu_table['drnu_lut'])
            step_size = drnu_table['dll_step_size'][()]
        return DRNUCompensation(lut, step_size)

    def compensate(self, image: np.ndarray):
        lut_index = image / self.step_size
        lut_index[lut_index > self.lut.shape[2]-1] -= self.lut.shape[2]
        floor_index = np.floor(lut_index).astype(int)
        ceil_index = np.ceil(lut_index).astype(int)
        # ceil_index[ceil_index >= self.lut.shape[2]]
        frac = lut_index - floor_index

        # linearly interpolate between the two closest values
        lower_error = self.lut[np.arange(self.lut.shape[0])[:, None],
                               np.arange(self.lut.shape[1]), floor_index]
        higher_error = self.lut[np.arange(self.lut.shape[0])[
            :, None], np.arange(self.lut.shape[1]), ceil_index]
        errors = higher_error * frac + lower_error * (1-frac)

        return image - errors


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
