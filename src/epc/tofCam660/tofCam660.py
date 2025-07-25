import numpy as np
import logging
from typing import Literal

from epc.tofCam_lib import TOFcam, TOF_Settings_Controller, Dev_Infos_Controller
from epc.tofCam_lib.decorator import requires_fw_version
from epc.tofCam660.interface import Interface, TcpReceiver, UdpInterface
from epc.tofCam660.memory import Memory
from epc.tofCam660.command import Command
from epc.tofCam_lib.projection_models import RadialCameraProjector
from epc.tofCam660.parser import (
    GrayscaleParser,
    DistanceParser,
    DistanceAndAmplitudeParser,
    DcsParser,
)

DEFAULT_IP_ADDRESS = "10.10.31.180"
DEFAULT_SUBNET_MASK = "255.255.255.0"
DEFAULT_GATEWAY = "0.0.0.0"
DEFAULT_TCP_PORT = 50660
DEFAULT_DATA_RX_PORT = 45454
DEFAULT_MAX_DEPTH = 16000
DEFAULT_MAX_AMP = 2894

log = logging.getLogger('TOFcam660')

class TOFcam660(TOFcam):
    """Creates a new TOFcam660 object and connects it to the ip address specified.

    If no ip address is specified, the default ip address (10.10.31.180) is used.

    The TOFcam660 object holds two attributes:

    - settings: allows to control the settings of the camera.
    - device: allows to get device information's of the camera.
    """
    def __init__(self, ip_address=DEFAULT_IP_ADDRESS):
        self.tcpInterface = Interface(ip_address, DEFAULT_TCP_PORT)
        self.rxInterface = UdpInterface(ip_address, DEFAULT_DATA_RX_PORT)
        self.settings = TOFcam660_Settings(self)
        self.device = TOFcam660_Device(self)
        super().__init__(self.settings, self.device)
        self.memory = Memory.create(0)
        self._version = self.device.get_fw_version()

    def __del__(self):
        if self.tcpInterface and not self.tcpInterface.is_socket_closed():
            self.tcpInterface.close()
        if self.rxInterface:
            self.rxInterface.close()

    def __get_image_date(self, command: Command):
        nBytes = 0
        for i in range(5):
            try:
                self.tcpInterface.transceive(command)
                frame_data, nBytes = self.rxInterface.receiveFrame()
                break
            except Exception as e:
                log.error(f"Failed to receive image data: {e}")
                continue
        if nBytes <= 0:
            raise RuntimeError("Failed to receive image data")
        return frame_data

    def initialize(self):
        self.settings.set_modulation(12)
        self.settings.set_roi((0, 0, 320, 240))
        self.settings.set_hdr(2)
        self.settings.set_modulation(frequency_mhz=12, channel=0)
        self.settings.set_integration_hdr([25, 40, 400, 2000])
        self.settings.set_minimal_amplitude(100)
        self.settings.disable_filters()
        self.settings.set_lense_type('Wide Field')

    def get_grayscale_image(self) -> np.ndarray:
        """ "Get a grayscale image from the camera as a 2d numpy array"""
        parser = GrayscaleParser()
        get_gray_command = Command.create("getGrayscale", self.settings.captureMode)
        raw_data = self.__get_image_date(get_gray_command)
        amplitude =  parser.parse(raw_data).amplitude
        return amplitude

    def get_distance_image(self) -> np.ndarray:
        """Get a distance image from the camera as a 2d numpy array. The distance is in mm."""
        parser = DistanceParser()
        get_dist_cmd = Command.create("getDistance", self.settings.captureMode)
        raw_data = self.__get_image_date(get_dist_cmd)
        distance =  parser.parse(raw_data).distance
        return distance

    def get_distance_and_amplitude(self) -> tuple[np.ndarray, np.ndarray]:
        """Get a distance and amplitude image from the camera as 2d numpy arrays. The distance is in mm."""
        parser = DistanceAndAmplitudeParser()
        get_dist_amp_cmd = Command.create(
            "getDistanceAndAmplitude", self.settings.captureMode
        )
        raw_data = self.__get_image_date(get_dist_amp_cmd)
        frame = parser.parse(raw_data)
        return frame.distance, frame.amplitude

    def get_amplitude_image(self) -> np.ndarray:
        """Get an amplitude image from the camera as a 2d numpy array."""
        return self.get_distance_and_amplitude()[1]

    def get_raw_dcs_images(self) -> np.ndarray:
        """Get a DCS image from the camera as a 2d numpy array."""
        parser = DcsParser()
        get_dcs_cmd = Command.create("getDcs", self.settings.captureMode)
        raw_data = self.__get_image_date(get_dcs_cmd)
        return parser.parse(raw_data).dcs
    
    def get_point_cloud(self) -> np.ndarray:
        """Returns a tuple holding point cloud from the camera as a 3xN numpy array and the corresponding amplitude values."""
        # capture depth image & corrections
        depth, amplitude = self.get_distance_and_amplitude()
        amplitude[amplitude>DEFAULT_MAX_AMP] = 0 # remove error codes
        depth  = depth.astype(np.float32)
        depth[depth >= self.settings.maxDepth] = np.nan
        depth = np.flipud(depth)
        amplitude = np.flipud(amplitude)

        # calculate point cloud from the depth image
        points = 1E-3 * self.settings.projector.project(depth, roi_x=self.settings.roi[0], roi_y=self.settings.roi[1])
        points = points.reshape(3, -1)
        return points, amplitude.flatten()


class TOFcam660_Settings(TOF_Settings_Controller):
    """The TOFcam660_Settings class is used to control the settings of the TOFcam660.
    """
    def __init__(self, cam: TOFcam660) -> None:
        super().__init__()
        self.roi = (0, 0, 320, 240)
        self.cam = cam
        self.captureMode = 0
        self.__int_time_grayscale = 50
        self.__int_time_low = 150
        self.__hdr_mode = 0
        self.projector = RadialCameraProjector.from_lens_calibration('Wide Field', self.roi[2], self.roi[3])
        self.maxDepth = DEFAULT_MAX_DEPTH

    def set_integration_time(self, int_time_us: int):
        """Set the integration time for standard mode in us."""
        if self.__hdr_mode != 0:
            raise ValueError(
                "Cannot set integration when HDR is on. use set_integration_hdr instead."
            )
        self.set_integration_hdr([self.__int_time_grayscale, int_time_us, 0, 0])

    def set_integration_time_grayscale(self, int_time_us: int):
        """Set the integration time for grayscale images in us."""
        if self.__hdr_mode != 0:
            raise ValueError(
                "Cannot set integration when HDR is on. use set_integration_hdr instead."
            )
        self.set_integration_hdr([int_time_us, self.__int_time_low, 0, 0])

    def set_integration_hdr(self, int_times: list[int]) -> None:
        """Set integration times for the camera.
        Args:
            int_times is a list of 4 integers: [grayscale, low, mid, high]
        """
        log.info(f"Setting integration times: {int_times}")
        self.cam.tcpInterface.transceive(
            Command.create(
                "setIntTimes",
                {
                    "lowIntTime": int_times[1],
                    "midIntTime": int_times[2],
                    "highIntTime": int_times[3],
                    "grayscaleIntTime": int_times[0],
                },
            )
        )
        self.__int_time_grayscale = int_times[0]
        self.__int_time_low = int_times[1]

    def set_roi(self, roi: tuple[int, int, int, int]):
        """Set the region of interest.
        Args:
            roi (tuple[int, int, int, int]): (x1, y1, x2, y2) where (x1, y1) is the top-left corner and (x2, y2) is the bottom-right corner.
        """
        if roi[1] != 240 - roi[3]:
            raise ValueError("TOFcam660 needs symetric y values")
        log.info(f"Setting ROI: {roi}")
        self.cam.tcpInterface.transceive(
            Command.create(
                "setRoi",
                {
                    "leftColumn": roi[0],
                    "topRow": roi[1],
                    "rightColumn": roi[2],
                    "bottomRow": roi[3],
                },
            )
        )
        self.roi = roi
        return self.roi

    def get_roi(self):
        """Returns the current region of interest.
        The ROI is a tuple of the form (x1, y1, x2, y2) where (x1, y1) is the top-left corner and (x2, y2) is the bottom-right corner.
        """
        return self.roi

    def set_hdr(self, mode: int) -> None:
        """Set the HDR mode for the camera.
        Args:
            mode (int): The mode to set. 0: off, 1: spatial, 2: temporal
        """
        if mode not in [0, 1, 2]:
            raise ValueError(f"Invalid HDR mode: {mode}. Must be 0, 1 or 2")
        log.info(f"Setting HDR mode: {mode}")
        self.cam.tcpInterface.transceive(Command.create("setHdr", mode))
        self.__hdr_mode = mode

    def set_binning(self, binning_type):
        log.info(f"Setting binning: {binning_type}")
        self.cam.tcpInterface.transceive(Command.create("setBinning", np.byte(binning_type)))

    def set_dll_step(self, step: int = 0):
        log.info(f"Setting DLL step: {step}")
        self.cam.tcpInterface.transceive(Command.create("setDllStep", step))

    def set_minimal_amplitude(self, minimum: int):
        """Set minimal amplitude needed to be considered a valid distance estimation."""
        log.info(f"Setting minimum amplitude: {minimum}")
        self.cam.tcpInterface.transceive(Command.create("setMinAmplitude", minimum))

    def set_grayscale_illumination(self, enable=True):
        """Enable or disable the illumination during grayscale capture."""
        log.info(f"Setting grayscale illumination: {enable}")
        self.cam.tcpInterface.transceive(Command.create("setGrayscaleIllumination", int(enable)))

    def set_compensations(
        self,
        setDrnuCompensation=True,
        setTemperatureCompensation=True,
        setAmbientLightCompensation=True,
        setGrayscaleCompensation=True,
    ):
        """Enable or distable compensations for the camera."""
        log.info('Changing compensations settings')
        self.cam.tcpInterface.transceive(
            Command.create(
                "setCompensation",
                {
                    "setDrnuCompensationEnabed": setDrnuCompensation,
                    "setTemperatureCompensationEnabled": setTemperatureCompensation,
                    "setAmbientLightCompensationEnabled": setAmbientLightCompensation,
                    "setGrayscaleCompensationEnabled": setGrayscaleCompensation,
                },
            )
        )

    def set_filters(
        self,
        enableMedianFilter: bool,
        enableAverageFilter: bool,
        edgeDetectionThreshold: int,
        temporalFilterFactor: int,
        temporalFilterThreshold: int,
        interferenceDetectionLimit: int,
        interferenceDetectionUseLastValue: bool,
    ):
        log.info('Changing filters settings')
        self.cam.tcpInterface.transceive(
            Command.create(
                "setFilter",
                {
                    "temporalFilterFactor": temporalFilterFactor,
                    "temporalFilterThreshold": temporalFilterThreshold,
                    "enableMedianFilter": enableMedianFilter,
                    "enableAverageFilter": enableAverageFilter,
                    "edgeDetectionThreshold": edgeDetectionThreshold,
                    "interferenceDetectionUseLastValue": interferenceDetectionUseLastValue,
                    "interferenceDetectionLimit": interferenceDetectionLimit,
                },
            )
        )

    def disable_filters(self):
        """Disable all filters."""
        log.info('Disabling filters')
        self.set_filters(False, False, 0, 0, 0, 0, False)

    def set_modulation(self, frequency_mhz: float, channel=0):
        """Set the modulation frequency and channel for the TOFcam."""
        freq_table = {
            12: 0,
            24: 1,
            6: 2,
            5: 0,  # for TOFcam660-H1
            3: 3,
            1.5: 4,
            0.75: 5,
        }
        try:
            frequency_code = freq_table[frequency_mhz]
        except KeyError:
            raise ValueError(
                f"Invalid frequency: {frequency_mhz}. Must be one of {list(freq_table.keys())}"
            )
        set_mod_cmd = Command.create(
            "setModulationFrequency",
            {"frequencyCode": frequency_code, "channel": channel},
        )
        log.info(f"Setting modulation frequency: {frequency_mhz} MHz, channel: {channel}")
        self.cam.tcpInterface.transceive(set_mod_cmd)

    def get_modulation_frequencies(self) -> list[float]:
        """Returns a list of available modulation frequencies in MHz."""
        return [0.75, 1.5, 3, 6, 12, 24]

    def get_modulation_channels(self) -> list[int]:
        """Returns a list of available modulation channels."""
        return list(range(0, 15))
    
    def set_lense_type(self, lense_type: int):
        """Set the lense type for the camera."""
        log.info(f"Setting lense type: {lense_type}")
        self.projector = RadialCameraProjector.from_lens_calibration(lense_type, self.roi[2], self.roi[3])


class TOFcam660_Device(Dev_Infos_Controller):
    """The TOFcam660_Device class is used to get and set device information's of the TOFcam660.
    """
    def __init__(self, cam: TOFcam660) -> None:
        super().__init__()
        self.cam = cam

    def write_register(self, reg_addr: int, value: int) -> None:
        """Write a value to a register on the epc660."""
        log.info(f"Writing to register 0x{reg_addr:02x}: 0x{value:02x}")
        self.cam.tcpInterface.transceive(
            Command.create("writeRegister", {"address": reg_addr, "value": value})
        )

    def read_register(self, reg_addr: int) -> int:
        """Read a value from a register on the epc660."""
        log.info(f"Reading from register 0x{reg_addr:02x}")
        reg_value = self.cam.tcpInterface.transceive(
            Command.create("readRegister", {"address": reg_addr})
        ).data
        return int(reg_value)
    
    def _calibrate(self) ->None:
        """Perform production calibration on the camera."""
        log.warning("Performing production calibration. Make sure the camera is mounted to the calibration box.")
        log.info("Performing production calibration")
        self.cam.tcpInterface.transceive(Command.create("calibrateProduction"))

    def get_chip_infos(self) -> tuple[int, int]:
        """Returns the chip id and wafer id of the epc660."""
        chipInfos = self.cam.tcpInterface.transceive(Command.create("readChipInformation")).data
        return chipInfos["chipid"], chipInfos["waferid"]

    def get_fw_version(self) -> str:
        """Returns the firmware version of the epc660."""
        fw_version = self.cam.tcpInterface.transceive(Command.create("readFirmwareRelease")).data
        return str(f"{fw_version['major']}.{fw_version['minor']}")

    def get_chip_temperature(self) -> float:
        """
        Returns the temperature of the epc660 chip in °C.

        WARNING: The temperature is only updated when a new frame is captured.
        """
        temp = self.cam.tcpInterface.transceive(Command.create("getTemperature")).data
        return float(temp)

    def system_reset(self):
        """Reset the camera."""
        log.warning("Resetting the camera")
        self.cam.tcpInterface.transmit(Command.create("systemReset"))

    def power_reset(self):
        """Powercycle the camera."""
        log.warning("Powercycling the camera")
        self.cam.tcpInterface.transmit(Command.create("powerReset"))

    def jump_to_bootloader(self):
        log.warning("Jumping to bootloader")
        self.cam.tcpInterface.transmit(Command.create("jumpToBootloader"))

    def set_udp_ip_address(self, ipAddress=DEFAULT_IP_ADDRESS):
        log.info(f"Setting UDP IP address: {ipAddress}")
        self.cam.tcpInterface.transceive(Command.create("setDataIpAddress", ipAddress))

    def set_camera_ip_address(
        self,
        ipAddress=DEFAULT_IP_ADDRESS,
        subnetMask=DEFAULT_SUBNET_MASK,
        gateway=DEFAULT_GATEWAY,
    ):
        log.info(f"Setting camera IP address: {ipAddress}")
        self.cam.tcpInterface.transceive(
            Command.create(
                "setCameraIpAddress",
                {"ipAddress": ipAddress, "subnetMask": subnetMask, "gateway": gateway},
            )
        )

    @requires_fw_version(min_version='3.43')
    def get_data_transfer_protocol(self):
        return self.cam.tcpInterface.transceive(Command.create("getDataTransferProtocol")).data

    @requires_fw_version(min_version='3.43')
    def set_data_transfer_protocol(self, transferInterface: Literal["UDP", "TCP"] = "UDP"):
        # If rx protocol is already set, only call Command
        if isinstance(self.cam.rxInterface, UdpInterface) and transferInterface == "UDP":
            self.cam.tcpInterface.transceive(Command.create("setDataTransferProtocol", {"selectTCP": 0}))
            return
        if isinstance(self.cam.rxInterface, TcpReceiver) and transferInterface == "TCP":
            self.cam.tcpInterface.transceive(Command.create("setDataTransferProtocol", {"selectTCP": 1}))
            return

        ip = self.cam.rxInterface.ip_address
        port = self.cam.rxInterface.port

        # Close previous transfer interface
        self.cam.rxInterface.close()

        # Open new transfer interface
        if transferInterface == "TCP":
            self.cam.tcpInterface.transceive(Command.create("setDataTransferProtocol", {"selectTCP": 1}))
            self.cam.rxInterface = TcpReceiver(ip, port)
        elif transferInterface == "UDP":
            self.cam.tcpInterface.transceive(Command.create("setDataTransferProtocol", {"selectTCP": 0}))
            self.cam.rxInterface = UdpInterface(ip, port)
        else: # unknown
            raise ValueError(f"{transferInterface} is not a valid rx_interface. Select either \'UDP\' or \'TCP\'")
