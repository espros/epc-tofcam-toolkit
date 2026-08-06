import enum
import logging
from typing import Protocol, Tuple

import numpy as np
from bumble.colors import none

from epc.tofCam_lib.projection_models import RadialCameraProjector
from epc.tofCam_lib.tofCam import Dev_Infos_Controller, TOF_Settings_Controller, TOFcam


class TOFControl(enum.Enum):
    """
    TOFCam Control ID's.
    """
    GAIN = 0
    ACQUISITION_MODE = 1
    MODULATION_FREQUENCY_HZ = 2
    EXPOSURE_US = 4
    HDR_INTEGRATION_TIME1_US = 5
    HDR_INTEGRATION_TIME2_US = 6
    HDR_INTEGRATION_TIME3_US = 7
    ENABLE_HDR_ROLLING_MODE = 8
    ENABLE_DCS_ROLLING_MODE = 9
    ENABLE_PHASE_OFFSET_COMPENSATION = 10
    ENABLE_PHASE_ERROR_COMPENSATION = 11
    ENABLE_TEMPERATURE_COMPENSATION = 12
    ENABLE_GRAYSCALE_DSNU_COMPENSATION = 13
    LED_DELAY_STEP = 14
    MIN_AMPLITUDE = 15
    INTERFERENCE_DETECTION_ENABLE = 16
    INTERFERENCE_DETECTION_THRESHOLD = 17
    INTERFERENCE_ENABLE_LATCHING = 18
    AVERAGE_FILTER_ENABLE = 19
    MEDIAN_FILTER_ENABLE = 20
    TEMPORAL_FILTER_ENABLE = 21
    TEMPORAL_FILTER_ALPHA = 22
    TEMPORAL_FILTER_THRESHOLD = 23
    KALMAN_FILTER_ENABLE = 24
    KALMAN_FILTER_THRESHOLD = 25
    KALMAN_FILTER_PROCESS_NOISE = 26
    EDGE_FILTER_ENABLE = 27
    EDGE_FILTER_THRESHOLD = 28


class FrameType(enum.Enum):
    """
    Frame data type selector for TOFFrame.get().
    """
    DCS = 0
    AMPLITUDE = 1
    DISTANCE = 2
    PHASE = 3
    GRAYSCALE = 4


class AcquisitionMode(enum.IntEnum):
    """
    Supported acquisition modes.
    """
    DIST_AMP = 0
    GRAYSCALE = 1
    DIST_AMP_HDR = 2
    DCS4 = 4


class Interface(Protocol):
    def set_control(self, control: TOFControl, value: int) -> None:
        ...

    def get_frame(self, frame_type: FrameType) -> np.ndarray[Tuple[int, int], float]:
        ...

    def get_distance_and_amplitude(self) -> tuple[np.ndarray, np.ndarray]:
        ...

    def startStream(self) -> None:
        ...

    def stopStream(self) -> None:
        ...


log = logging.getLogger(__name__)

DEFAULT_MAX_AMP = 2894
DEFAULT_MAX_DEPTH = 64000


class TOFcam670Settings(TOF_Settings_Controller):
    """
    Shared TOFcam670 settings logic. Subclasses need to implement `_set_control`.
    """

    def __init__(self, cam: "TOFcam670") -> None:
        super().__init__()
        self.cam = cam
        self.max_depth = DEFAULT_MAX_DEPTH
        self.roi = (0, 0, 320, 240)
        self._current_acquisition_mode = AcquisitionMode.DIST_AMP_HDR

    def _set_control(self, control: TOFControl, value: int) -> None:
        self.cam.interface.set_control(control, value)

    def get_roi(self):
        """ Get the current region of interest (ROI) for the TOFcam670 device. """
        return self.roi

    def set_integration_time(self, int_time_us: int):
        """ Set the integration time for the TOFcam670 device. Expects a single integration time in microseconds."""
        self._set_control(TOFControl.EXPOSURE_US, int_time_us)
        log.info("Set integration time to: %d us", int_time_us)

    def set_integration_hdr(self, int_times: list[int]) -> None:
        """ Set the integration times for HDR mode. Expects a list of three integration times in microseconds."""
        self._set_control(TOFControl.HDR_INTEGRATION_TIME1_US, int_times[0])
        self._set_control(TOFControl.HDR_INTEGRATION_TIME2_US, int_times[1])
        self._set_control(TOFControl.HDR_INTEGRATION_TIME3_US, int_times[2])
        log.info("Set hdr integration times to: %s us", str(int_times))

    def set_integration_time_grayscale(self, int_time_us: int):
        """ Set the integration time for grayscale mode."""
        self._set_control(TOFControl.EXPOSURE_US, int_time_us)
        log.info("Set grayscale integration time to: %d us", int_time_us)

    def set_hdr(self, mode):
        """ Set the HDR mode of the TOFcam670 device. Mode 0: DIST_AMP, Mode 2: DIST_AMP_HDR. """
        if mode == 0:
            self._current_acquisition_mode = AcquisitionMode.DIST_AMP
        elif mode == 2:
            self._current_acquisition_mode = AcquisitionMode.DIST_AMP_HDR
        else:
            raise ValueError(f"Unsupported HDR mode: {mode}")

        self.set_acquisition_mode(self._current_acquisition_mode)

    def set_minimal_amplitude(self, amplitude):
        """Set the minimal amplitude for the TOFcam670 device."""
        self._set_control(TOFControl.MIN_AMPLITUDE, amplitude)

    def set_dcs_rolling_mode(self, enabled=False):
        """Set DCS rolling mode."""
        self._set_control(TOFControl.ENABLE_DCS_ROLLING_MODE, int(enabled))

    def set_hdr_rolling_mode(self, enabled=False):
        """Set HDR rolling mode."""
        self._set_control(TOFControl.ENABLE_HDR_ROLLING_MODE, int(enabled))

    def set_lense_type(self, lense_type: str):
        """Set the lens type for the TOFcam670 device."""
        self.cam.projector = RadialCameraProjector.from_lens_calibration(lense_type, 320, 240)

    def set_modulation(self, frequency_mhz: float):
        """Set the modulation frequency of the TOFcam670 device."""
        self._set_control(TOFControl.MODULATION_FREQUENCY_HZ, int(frequency_mhz * 1e6))

    def set_acquisition_mode(self, mode: AcquisitionMode):
        """ Set the acquisition mode of the TOFcam670 device."""
        log.info("Setting acquisition mode to: %s", mode.name)
        self._set_control(TOFControl.ACQUISITION_MODE, mode)

    def set_average_filter(self, enabled=False):
        """Set average filter settings."""
        self._set_control(TOFControl.AVERAGE_FILTER_ENABLE, int(enabled))

    def set_median_filter(self, enabled=False):
        """Set median filter settings."""
        self._set_control(TOFControl.MEDIAN_FILTER_ENABLE, int(enabled))

    def set_kalman_filter(self, enabled=False, threshold=200):
        """Set Kalman filter settings."""
        self._set_control(TOFControl.KALMAN_FILTER_ENABLE, int(enabled))
        self._set_control(TOFControl.KALMAN_FILTER_THRESHOLD, int(threshold))

    def set_edge_filter(self, enabled=False, threshold=150):
        """Set edge filter settings."""
        self._set_control(TOFControl.EDGE_FILTER_ENABLE, int(enabled))
        self._set_control(TOFControl.EDGE_FILTER_THRESHOLD, int(threshold))

    def set_temporal_filter(self, enabled=False, alpha=0.3):
        """Set temporal filter settings."""
        self._set_control(TOFControl.TEMPORAL_FILTER_ENABLE, int(enabled))
        self._set_control(TOFControl.TEMPORAL_FILTER_ALPHA, int(alpha * 100))

    def set_interference_filter(self, enabled=False, threshold=300, latching=False):
        """Set interference filter settings."""
        self._set_control(TOFControl.INTERFERENCE_DETECTION_ENABLE, int(enabled))
        self._set_control(TOFControl.INTERFERENCE_DETECTION_THRESHOLD, int(threshold))
        self._set_control(TOFControl.INTERFERENCE_ENABLE_LATCHING, int(latching))


class TOFcam670Device(Dev_Infos_Controller):
    """
    Shared TOFcam670 device info logic. Subclasses need to implement `_get_device_info`.
    """

    def __init__(self, cam: "TOFcam670") -> None:
        super().__init__()
        self.cam = cam

    def get_chip_infos(self):
        """ Get the wafer ID and chip ID of the TOFcam670 device."""
        info = self.cam.interface.get_device_info()
        return info["wafer_id"], info["chip_id"]

    def get_fw_version(self):
        """ Get the firmware version of the TOFcam670 device."""
        info = self.cam.interface.get_device_info()
        return info["fw_version"]


class TOFcam670(TOFcam):

    def __init__(self, ip_addr=None, port=8000) -> None:
        if ip_addr is not None and port is not None:
            log.info("Using WebInterface for IP: %s, Port: %d", ip_addr, port)
            from epc.tofCam670.webInterface import WebInterface
            self.interface = WebInterface(ip_addr, port)
        else:
            log.info("Using NativeTOFcam670Interface")
            try:
                from epc.tofCam670.nativeInterface import NativeInterface
            except ImportError as e:
                e.add_note("Failed to import the native implementation of TOFcam670.")
                e.add_note("The Native implementation is meant to run directly on the"
                           "TOFcam670 device and requires the 'epc_tofcam_native' library.")
                e.add_note("If you meant to connect to a remote camera instead, "
                           "use the '--ip' option to specify a remote ip address.")
                raise e

            self.interface = NativeInterface()

        settings = TOFcam670Settings(self)
        device = TOFcam670Device(self)
        super().__init__(settings, device)
        self.projector = RadialCameraProjector.from_lens_calibration('Wide Field', 320, 240)

    def __del__(self):
        try:
            self.interface.stop_stream()
        except Exception as e:
            log.warning(f"Failed to stop stream during cleanup: {e}")

    def initialize(self):
        pass

    def get_distance_image(self):
        """ get distance image in mm, with error codes removed (set to NaN) """
        distance = self.interface.get_frame(FrameType.DISTANCE).astype(float)
        result = distance
        result[distance > self.settings.max_depth] = np.nan

        # images with only NaN values would crash
        if np.all(np.isnan(result)):
            result = np.zeros_like(result)

        return result

    def get_amplitude_image(self):
        """ get amplitude image, with error codes removed (set to NaN) """
        return self.interface.get_frame(FrameType.AMPLITUDE)

    def get_grayscale_image(self):
        """ get grayscale image """
        return self.interface.get_frame(FrameType.GRAYSCALE)

    def get_raw_dcs_images(self):
        """ get raw DCS images """
        return self.interface.get_frame(FrameType.DCS)

    def get_point_cloud(self):
        """ get point cloud in meters, with error codes removed (set to NaN) """
        depth, amplitude = self.interface.get_distance_and_amplitude()
        depth = depth.astype(float)
        amplitude = amplitude.astype(float)

        depth[depth >= self.settings.max_depth] = np.nan  # remove error codes
        amplitude[amplitude > DEFAULT_MAX_AMP] = np.nan  # remove error codes

        depth = np.flipud(depth)
        amplitude = np.flipud(amplitude)

        # calculate point cloud from the depth image
        points = 1E-3 * self.projector.project(
            depth=depth,
            roi_x=self.settings.roi[0],
            roi_y=self.settings.roi[1],
        )
        points = points.reshape(3, -1)
        return points, amplitude.flatten()
