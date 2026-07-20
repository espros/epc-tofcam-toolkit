import warnings
import numpy as np
from enum import Enum
from datetime import timedelta
from epc.tofCam_lib import TOFcam, TOF_Settings_Controller, Dev_Infos_Controller
from epc.tofCam_lib.filters import TemporalFilter, edgeFilter
from typing import Optional, Union, cast

from epc.hawkeyeBt.communication.bluetooth import BluetoothCam, ControlPointDataInterface, ControlPointHandler
from scipy.ndimage import median_filter, uniform_filter, vectorized_filter

class Hawkeye_Settings(TOF_Settings_Controller):
    def __init__(self, cam: "HawkeyeBt") -> None:
        super().__init__()
        self.cam = cam

    def set_modulation(self, frequency_mhz: float, channel: int = 0):
        """Set the modulation frequency and channel for the camera."""
        frequency_hz = int(frequency_mhz * 1000000)
        self.cam.bt_cam.set_modulation_frequency_hz(frequency_hz)

    def get_modulation_frequency(self) -> Optional[float]:
        """Reads the currently set modulation frequency back from the camera."""
        frequency_hz = self.cam.bt_cam.get_modulation_frequency_hz()
        if frequency_hz is not None:
            frequency_mhz = float(frequency_hz / 1000000)
            return frequency_mhz
        return None

    def get_modulation_frequencies(self) -> list[float]:
        """Returns a list of available modulation frequencies in MHz."""
        return [10, 20]

    def get_roi(self) -> Optional[tuple[int, int, int, int]]:
        """Returns the current region of interest.
        The ROI is a tuple of the form (x1, y1, x2, y2) where (x1, y1) is the top-left corner ⇱ and (x2, y2) is the bottom-right ⇲ corner.
        """
        return self.cam.bt_cam.get_roi()
    
    def set_roi(self, roi: tuple[int, int, int, int]):
        """Set the region of interest.
        Args:
            roi (tuple[int, int, int, int]): (x1, y1, x2, y2) where (x1, y1) is the top-left corner ⇱ and (x2, y2) is the bottom-right ⇲ corner.
        """
        self.cam.bt_cam.set_roi(roi)

    def set_minimal_amplitude(self, amplitude: int):
        """Set minimal amplitude needed to be considered a valid distance estimation."""
        self.cam.bt_cam.set_min_amplitude(amplitude)

    def set_integration_time(self, int_time_us: int):
        """Set the integration time in us."""
        self.cam.bt_cam.set_integration_time(int_time_us)

    def set_compensations(
        self,
        setPhaseOffsetCompensation: bool = True,
        setPhaseErrorCompensation: bool = True,
        setTemperatureCompensation: bool = True,
        setGrayscaleDsnuCompensation: bool = True,
    ):
        """Enable or disable compensations for the camera."""
        self.cam.bt_cam.set_compensation_phase_offset(setPhaseOffsetCompensation)
        self.cam.bt_cam.set_compensation_phase_error(setPhaseErrorCompensation)
        self.cam.bt_cam.set_compensation_temperature(setTemperatureCompensation)
        self.cam.bt_cam.set_compensation_grayscale_dsnu(setGrayscaleDsnuCompensation)

class Hawkeye_Device(Dev_Infos_Controller):
    class __DeviceInformation():
        WaferId: int
        ChipId: int
        ChipType: int
        DeviceType: int
        PcbVersion : str
        FwVersion : str
        isReady: bool = False

    def __init__(self, cam: "HawkeyeBt") -> None:
        super().__init__()
        self.cam = cam
        self.devInfo = self.__DeviceInformation()

    def __get_device_information(self):
        if self.devInfo.isReady is not True:
            self.devInfo.WaferId, self.devInfo.ChipId, self.devInfo.ChipType, self.devInfo.DeviceType, self.devInfo.PcbVersion, self.devInfo.FwVersion = self.cam.get_device_information()
            self.devInfo.isReady = True

    def get_chip_infos(self) -> tuple[int, int]:
        """returns chip information

        Returns:
            tuple[int, int]: chipId, waferId
        """
        self.__get_device_information()
        return (self.devInfo.ChipId, self.devInfo.WaferId)

    def get_fw_version(self) -> str:
        """returns firmware version as string"""
        self.__get_device_information()
        return self.devInfo.FwVersion

    def get_device_id(self) -> str:
        """returns device id

        Returns:
            A string containing PCB version, device type and chip type
        """
        self.__get_device_information()
        return f'PCB Version: {self.devInfo.PcbVersion}, Device Type: {self.devInfo.DeviceType}, Chip Type: {self.devInfo.ChipType}'

class HawkeyeBt(TOFcam):
    class __ApplicationControlPointData(ControlPointDataInterface):
        Uuid = "0000FE54-2AC6-4541-9D4C-21EDAE82ED19"
        class Commands(Enum):
            GET_CONTROL = 0x01
            SET_CONTROL = 0x02

        class SubCommands(Enum):
            OUTPUT_SELECTION_MASK = 0x01
            UPTIME = 0x02             # read only
            TEMPERATURE = 0x03        # read only

        class OutputType():
            amplitude_only = b'\x01'
            distance_only = b'\x02'
            distance_amplitude = b'\x03'
            grayscale_only = b'\x04'
    
    settings: Hawkeye_Settings
    device: Hawkeye_Device

    def __init__(self, mac_address: str) -> None:
        self.bt_cam = BluetoothCam(mac_address)
        self.current_output_type = b'\x00'
        self.settings = Hawkeye_Settings(self)
        self.device = Hawkeye_Device(self)
        super().__init__(self.settings, self.device)
        self.AppCpData = self.__ApplicationControlPointData
        self.application_controlpoint_handler = ControlPointHandler(self.bt_cam, self.AppCpData)
        self.maxDepth = 16000
        self.medianFilterOn = False
        self.averageFilterOn = False
        self.edgeFilterOn = False
        self.edgeFilterThreshold = 300
        self.temporalFilterOn = False
        self.temporalFilter = TemporalFilter()
        self.latestMetadata = None

    def __del__(self):
        pass

    def __enter__(self):
        self.bt_cam.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            camera = self.bt_cam
        except AttributeError:
            camera = None
        if camera:
            if camera.bt_dev and camera.bt_dev.is_connected():
                camera.bt_dev.unregister_notification(char_uuid=self.AppCpData.Uuid)
            camera.__exit__(exc_type, exc_val, exc_tb)

    def initialize(self):
        self.bt_cam.bt_dev.register_notification(char_uuid=self.AppCpData.Uuid, callback=self.bt_cam.on_notification)
        self.__set_output_type(self.AppCpData.OutputType.distance_only)
        self.bt_cam.start_stream()

    def __get_image(self):
        for _ in range(3):
            img = self.bt_cam.get_image()
            if img is not None:
                return img
        w = self.bt_cam._roi[2] - self.bt_cam._roi[0] + 1
        h = self.bt_cam._roi[3] - self.bt_cam._roi[1] + 1
        return np.zeros((w, h))

    def get_distance_image(self):
        """returns a distance image as a 2d numpy array"""
        self.__set_output_type(self.AppCpData.OutputType.distance_only)
        frame = self.__get_image().astype(float)
        frame[frame > self.maxDepth] = np.nan
        if (self.averageFilterOn):
            # use np.nanmean because scipy uniformfilter cannot handle NaN values
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', 'Mean of empty slice')
                frame = vectorized_filter(frame, function=np.nanmean, size=3)
        if (self.medianFilterOn):
            frame = median_filter(frame, size=3)
        if (self.temporalFilterOn):
            frame = self.temporalFilter(frame)
        if self.edgeFilterOn:
            frame = edgeFilter(frame, threshold=self.edgeFilterThreshold)
        return frame

    def get_amplitude_image(self):
        """returns an amplitude image as a 2d numpy array"""
        self.__set_output_type(self.AppCpData.OutputType.amplitude_only)
        frame = self.__get_image()
        if (self.averageFilterOn):
            frame = uniform_filter(frame, size=3)
        if (self.medianFilterOn):
            frame = median_filter(frame, size=3)
        if (self.temporalFilterOn):
            frame = self.temporalFilter(frame)
        if self.edgeFilterOn:
            frame = edgeFilter(frame, threshold=self.edgeFilterThreshold)
        return frame

    def get_grayscale_image(self):
        """returns an grayscale image as a 2d numpy array"""
        self.__set_output_type(self.AppCpData.OutputType.grayscale_only)
        frame = self.__get_image() - 2048
        if (self.averageFilterOn):
            frame = uniform_filter(frame, size=3)
        if (self.medianFilterOn):
            frame = median_filter(frame, size=3)
        if (self.temporalFilterOn):
            frame = self.temporalFilter(frame)
        if self.edgeFilterOn:
            frame = edgeFilter(frame, threshold=self.edgeFilterThreshold)
        return frame
    
    def __set_output_type(self, mask: Union[__ApplicationControlPointData.OutputType, bytes]):
        if mask != self.current_output_type:
            self.current_output_type = cast(bytes, mask)
            self.application_controlpoint_handler.set_control(self.AppCpData.SubCommands.OUTPUT_SELECTION_MASK, self.current_output_type)

    def get_device_information(self)-> tuple[int, int, int, int, str, str]:
        """returns device information

        Returns:
            tuple[int, int, int, int, str, str]: WaferId, ChipId, ChipType, DeviceType, PcbVersion (3 bytes), FwVersion (3 bytes)
        """
        raw_data = self.bt_cam.bt_dev.read_gatt_char('0000FE54-2AC4-4541-9D4C-21EDAE82ED19')
        return (raw_data[0],
                raw_data[1],
                raw_data[2],
                raw_data[3],
                f"{raw_data[4]}.{raw_data[5]}.{raw_data[6],}",
                f"{raw_data[7]}.{raw_data[8]}.{raw_data[9],}",
                )

    def get_uptime(self) -> timedelta:
        """Returns the timedelta since the camera booted up in seconds."""
        raw_data = self.application_controlpoint_handler.get_control(self.AppCpData.SubCommands.UPTIME, 4)
        if raw_data is not None:
            uptime_in_seconds = int.from_bytes(raw_data[0:4], 'big', signed=False)
            return timedelta(seconds=uptime_in_seconds)
        return timedelta(seconds=0)
    
    def get_temperature(self) -> float:
        """Returns the temperature of the camera in Degrees Celsius."""
        raw_data = self.application_controlpoint_handler.get_control(self.AppCpData.SubCommands.TEMPERATURE, 4)
        if raw_data is not None:
            temperature_millicelsius = int.from_bytes(raw_data[0:4], 'big', signed=False)
            return temperature_millicelsius / 1000
        return 0.0