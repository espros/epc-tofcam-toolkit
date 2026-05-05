from epc.tofCam_lib.tofCam import TOFcam, Dev_Infos_Controller, TOF_Settings_Controller
from epc.tofCam_lib.projection_models import RadialCameraProjector
from epc_tofcam_native import TOFCam as libcam
from epc_tofcam_native import TOFControl, TOFFrame, FrameType, AcquisitionMode
import numpy as np
import logging
import subprocess
from scipy.ndimage import median_filter, uniform_filter

DEFAULT_MAX_AMP = 2894
DEFAULT_MAX_DEPTH = 16000

log = logging.getLogger('TOFcam670')
libLogger = logging.getLogger('epc_tofcam_native').setLevel(logging.DEBUG)


class TOFcam670_Settings(TOF_Settings_Controller):
    def __init__(self, cam: "TOFcam670") -> None:
        super().__init__()
        self.cam = cam
        self.maxDepth = DEFAULT_MAX_DEPTH
        self.roi = (0, 0, 320, 240)
        self._current_acquisition_mode = AcquisitionMode.DIST_AMP_HDR

    def get_roi(self):
        return self.roi

    def set_integration_time(self, int_time_us: int):
        self.cam.cam.setControl(TOFControl.EXPOSURE_US, int_time_us)
        log.info(f"Set integration time to: {int_time_us} us")

    def set_integration_hdr(self, int_times: list[int]) -> None:
        self.cam.cam.setControl(TOFControl.HDR_INTEGRATION_TIME1_US, int_times[0])
        self.cam.cam.setControl(TOFControl.HDR_INTEGRATION_TIME2_US, int_times[1])
        self.cam.cam.setControl(TOFControl.HDR_INTEGRATION_TIME3_US, int_times[2])
        log.info(f"Set hdr integration times to: {int_times} us")

    def set_integration_time_grayscale(self, int_time_us: int):
        self.cam.cam.setControl(TOFControl.EXPOSURE_US, int_time_us)
        log.info(f"Set grayscale integration time to: {int_time_us} us")

    def set_hdr(self, mode):
        if mode == 0:
            self._current_acquisition_mode = AcquisitionMode.DIST_AMP
        elif mode == 2:
            self._current_acquisition_mode = AcquisitionMode.DIST_AMP_HDR
        else:
            raise ValueError(f"Unsupported HDR mode: {mode}")
        
        self.set_acquisition_mode(self._current_acquisition_mode)
    
    def set_minimal_amplitude(self, amplitude):
        self.cam.cam.setControl(TOFControl.MIN_AMPLITUDE, amplitude)

    def set_lense_type(self, lense_type: str):
        self.cam.projector = RadialCameraProjector.from_lens_calibration(lense_type, 320, 240)

    def set_modulation(self, frequency_mhz: float):
        self.cam.cam.setControl(TOFControl.MODULATION_FREQUENCY_HZ, int(frequency_mhz*1e6))

    def set_acquisition_mode(self, mode: AcquisitionMode):
        log.info(f"Setting acquisition mode to: {mode.name}")
        self.cam.cam.setControl(TOFControl.ACQUISITION_MODE, mode)

class TOFcam670_Device(Dev_Infos_Controller):
    def __init__(self, cam: TOFcam) -> None:
        super().__init__()
        self.cam = cam

    def get_chip_infos(self):
        try:
            result = subprocess.run(
                ["v4l2-ctl", "-d", "/dev/v4l-subdev2", "-C", "device_id"],
                capture_output=True, text=True, timeout=5
            )
            device_id = result.stdout.strip()
            # Format: "device_id: 'epc670-0x00-0x04-0x0F-0x00-00008-00105'"
            parts = device_id.split('-')
            wafer_id = int(parts[-2])
            chip_id = int(parts[-1].rstrip("'"))
            return chip_id, wafer_id
        except Exception as e:
            log.error(f"Failed to get chip infos: {e}")
            return 0, 0

    def get_fw_version(self):
        try:
            with open("/sys/module/cam_epc670/version", "r") as f:
                return f.read().strip()
        except OSError:
            return "0.0.0"


class TOFcam670(TOFcam):
    def __init__(self) -> None:
        self.cam = libcam()
        self.cam.open()
        self.__acquisition_mode = AcquisitionMode.DIST_AMP_HDR
        self.cam.setControl(TOFControl.ACQUISITION_MODE, self.__acquisition_mode)
        self.settings = TOFcam670_Settings(self)
        self.device = TOFcam670_Device(self)
        super().__init__(self.settings, self.device)
        self.projector = RadialCameraProjector.from_lens_calibration('Wide Field', 320, 240)
        self.medianFilterOn = False
        self.averageFilterOn = False
        self.latestMetadata = None

    def __del__(self):
        # self.cam.stopStream()
        self.cam.close()

    def initialize(self):
        self.settings.set_modulation(10)
        pass

    def __capture_frame(self):
        frame = self.cam.captureFrame()
        self.latestMetadata = frame.getMetadata()
        return frame

    def get_distance_image(self):
        frame = self.__capture_frame()
        distance = frame.get(FrameType.DISTANCE)
        result = np.where(distance < self.settings.maxDepth, distance, 0)
        if (self.medianFilterOn):
            result = median_filter(result, size=3)
        if (self.averageFilterOn):
            result = uniform_filter(result, size=3)
        return result

    def get_amplitude_image(self):
        frame = self.__capture_frame()
        amplitude = frame.get(FrameType.AMPLITUDE)
        if (self.medianFilterOn):
            amplitude = median_filter(amplitude, size=3)
        if (self.averageFilterOn):
            amplitude = uniform_filter(amplitude, size=3)
        return amplitude

    def get_grayscale_image(self):
        frame = self.__capture_frame()
        grayscale = frame.get(FrameType.GRAYSCALE)
        return grayscale

    def get_raw_dcs_images(self):
        frame = self.__capture_frame()
        dcs0 = frame.get(FrameType.DCS, 0)
        dcs1 = frame.get(FrameType.DCS, 1)
        dcs2 = frame.get(FrameType.DCS, 2)
        dcs3 = frame.get(FrameType.DCS, 3)

        return np.array([dcs0, dcs1, dcs2, dcs3])

    def get_point_cloud(self):
        frame = self.__capture_frame()
        depth = frame.get(FrameType.DISTANCE)
        amplitude = frame.get(FrameType.AMPLITUDE)
        if (self.medianFilterOn):
            depth = median_filter(depth, size=3)
        if (self.averageFilterOn):
            depth = uniform_filter(depth, size=3)

        amplitude[amplitude>DEFAULT_MAX_AMP] = 0 # remove error codes
        depth  = depth.astype(np.float32)
        depth[depth >= self.settings.maxDepth] = np.nan
        depth = np.flipud(depth)
        amplitude = np.flipud(amplitude)

        # calculate point cloud from the depth image
        points = 1E-3 * self.projector.project(depth, roi_x=self.settings.roi[0], roi_y=self.settings.roi[1])
        points = points.reshape(3, -1)
        return points, amplitude.flatten()

if __name__ == "__main__":
    cam = TOFcam670()
    cam.initialize()
    distance_image = cam.get_distance_image()
    amplitude_image = cam.get_amplitude_image()
    grayscale_image = cam.get_grayscale_image()
    raw_dcs_images = cam.get_raw_dcs_images()
    point_cloud = cam.get_point_cloud()

    print("Distance Image shape:", distance_image.shape)
    print("Amplitude Image shape:", amplitude_image.shape)
    print("Grayscale Image shape:", grayscale_image.shape)
    print("Raw DCS Images shape:", raw_dcs_images.shape)
    print("Point Cloud shape:", point_cloud.shape if point_cloud is not None else None)