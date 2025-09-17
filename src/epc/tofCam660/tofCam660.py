import numpy as np
import logging
import time
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

MAX_DCS_VALUE = 64000
C = 299792458
TOF_COS_DISTANCE_CHIP_TO_FRONT = 28.0
TOF_COS_CALIBRATION_BOX_LENGTH = 330.0
TOF_COS_TEMPERATURE_COEFFICIENT = 12.9 + 4.6

CONST_OFFSET_CORRECTION = TOF_COS_CALIBRATION_BOX_LENGTH-TOF_COS_DISTANCE_CHIP_TO_FRONT - 7/8*12500

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
        self._calibData = self.device.get_calibration_data()
        self._calibData24Mhz: dict = next((item for item in self._calibData if item['modulation(MHz)'] == 24), None)
        assert self._calibData24Mhz is not None, "Calibration data for 24 MHz not found"

        self.frame = None


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
        self.settings._store_dll_settings()
        self.settings._store_abs_setting()
        self.settings.set_modulation(3)
        self.settings.set_roi((0, 0, 320, 240))
        self.settings.set_hdr(0)
        self.settings.set_modulation(frequency_mhz=3, channel=0)
        self.settings.set_integration_hdr([25, 16, 0, 0])
        integrationTimes = self.settings.get_integration_time()
        assert integrationTimes['grayscaleIntTime'] == 25, "Grayscale integration time not set correctly"
        assert integrationTimes['lowIntTime'] == 16, "Low integration time not set correctly"
        assert integrationTimes['midIntTime'] == 0, "Mid integration time not set correctly"
        assert integrationTimes['highIntTime'] == 0, "High integration time not set correctly"


        self.settings.set_minimal_amplitude(100)
        self.settings.disable_filters()
        self.settings.set_compensations(setDrnuCompensation=True,
                                        setTemperatureCompensation=True,
                                        setAmbientLightCompensation=True,
                                        setGrayscaleCompensation=True)
        self.settings.set_lense_type('Wide Field')
        self.settings.set_binning(0)
        self.get_raw_dcs_images()  # trigger first image to initialize the camera

    @requires_fw_version(min_version='3.50')
    def get_flex_mod_distance_amplitude_dcs(self, 
                                            calibData: dict, 
                                            modFreq_MHz: int, 
                                            minAmp: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Acquire a DCS image with a flexibly chosen modulation frequency and calculate the distance and amplitude images from it."""
        log.info(f"Get image with modulation frequency {modFreq_MHz} MHz.")
        dcs = self.get_raw_dcs_images()
        temp = self.device.get_chip_temperature()

        # create masks for certain flags (part 1/2)
        mask_overflow = np.logical_or.reduce(dcs == 64002)
        mask_saturation = np.logical_or.reduce(dcs == 64003)
        
        # filter invalid values
        dcs = dcs.astype(np.float32)
        dcs[dcs >= MAX_DCS_VALUE] = np.nan

        # calculate amplitude
        diff0 = dcs[2] - dcs[0]
        diff1 = dcs[3] - dcs[1]
        amplitude = np.sqrt(diff0**2 + diff1**2) / 2

        # create masks for certain flags (part 2/2)
        mask_low_amplitude = amplitude <= minAmp
        
        # calculate phase
        phi = np.arctan2(diff1, diff0) + np.pi
        phi[amplitude < minAmp] = np.nan 

        # calculate distance
        unambiguity_mm = (C / (2 * modFreq_MHz * 1E6)) * 1000
        distance = (phi * unambiguity_mm) / (2 * np.pi)

        # compensate offsets
        temp_offset = (calibData['calibrated_temperature(mDeg)']/1000 - temp) * TOF_COS_TEMPERATURE_COEFFICIENT
        distance = distance + (6250 - calibData['atan_offset']) + temp_offset + CONST_OFFSET_CORRECTION
        
        # handle unambiguity steps
        distance %= unambiguity_mm

        # apply the masks for the error codes (keep the order!)
        amplitude[mask_overflow] = 64002
        amplitude[mask_saturation] = 64003
        distance[mask_low_amplitude] = 64001
        distance[mask_overflow] = 64002
        distance[mask_saturation] = 64003

        # assign our calculated values to the frame
        self.frame.amplitude = amplitude
        self.frame.distance = distance

        return (distance, amplitude, dcs)

    def get_grayscale_image(self) -> np.ndarray:
        """ "Get a grayscale image from the camera as a 2d numpy array"""
        parser = GrayscaleParser()
        get_gray_command = Command.create("getGrayscale", self.settings.captureMode)
        raw_data = self.__get_image_date(get_gray_command)
        self.frame = parser.parse(raw_data)
        return self.frame.amplitude

    def get_distance_image(self) -> np.ndarray:
        """Get a distance image from the camera as a 2d numpy array. The distance is in mm."""
        if not self.settings.flexMod:
            parser = DistanceParser()
            get_dist_cmd = Command.create("getDistance", self.settings.captureMode)
            raw_data = self.__get_image_date(get_dist_cmd)
            self.frame = parser.parse(raw_data)
            return self.frame.distance
        else:
            dist, _, = self.get_distance_and_amplitude()
            return dist

    def get_distance_and_amplitude(self) -> tuple[np.ndarray, np.ndarray]:
        """Get a distance and amplitude image from the camera as 2d numpy arrays. The distance is in mm."""
        if not self.settings.flexMod:
            parser = DistanceAndAmplitudeParser()
            get_dist_amp_cmd = Command.create(
                "getDistanceAndAmplitude", self.settings.captureMode
            )
            raw_data = self.__get_image_date(get_dist_amp_cmd)
            self.frame = parser.parse(raw_data)
            return self.frame.distance, self.frame.amplitude
        else:
            dist, amplitude, _ = self.get_flex_mod_distance_amplitude_dcs(self._calibData24Mhz, 
                                                                          self.settings.flexModFreq_MHz, 
                                                                          self.settings.minAmplitude
                                                                          )
            return dist, amplitude

    def get_amplitude_image(self) -> np.ndarray:
        """Get an amplitude image from the camera as a 2d numpy array."""
        return self.get_distance_and_amplitude()[1]

    def get_raw_dcs_images(self) -> np.ndarray:
        """Get a DCS image from the camera as a 2d numpy array."""
        parser = DcsParser()
        get_dcs_cmd = Command.create("getDcs", self.settings.captureMode)
        raw_data = self.__get_image_date(get_dcs_cmd)
        self.frame = parser.parse(raw_data)
        return self.frame.dcs

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
        self.flexMod = False
        self.flexModFreq_MHz = 0.0
        self.intTime_us = 0
        self.minAmplitude = 0
        self.dllRegisterSettings = {
            0x71: 0x00,
            0x72: 0x00,
            0x73: 0x00,
            0x8b: 0x00,
            0x93: 0x00        }
        self.absRegisterSetting = {
            0x88: 0x00,
        }
    
    def _clear_dll_settings(self):
        """Clear the DLL settings in the camera."""
        for reg, value in self.dllRegisterSettings.items():
            self.cam.tcpInterface.transceive(Command.create("writeRegister", {"address": reg, "value": 0x00}))

    def _store_dll_settings(self):
        """Store the current DLL settings in the camera."""
        for reg in self.dllRegisterSettings.keys():
            regValue = self.cam.tcpInterface.transceive(Command.create("readRegister", {"address": reg})).data
            self.dllRegisterSettings[reg] = int(regValue)
    
    def _restore_dll_settings(self):
        """Restore the DLL settings in the camera."""
        for reg, value in self.dllRegisterSettings.items():
            self.cam.tcpInterface.transceive(Command.create("writeRegister", {"address": reg, "value": value}))

    def _store_abs_setting(self):
        """Store the current camera ABS pixel ramp setting."""
        for reg in self.absRegisterSetting.keys():
            regValue = self.cam.tcpInterface.transceive(Command.create("readRegister", {"address": reg})).data
            self.absRegisterSetting[reg] = int(regValue)
    
    def _restore_abs_setting(self):
        """Restore the ABS pixel ramp setting in the camera."""
        for reg, value in self.absRegisterSetting.items():
            self.cam.tcpInterface.transceive(Command.create("writeRegister", {"address": reg, "value": value}))

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
        self.intTime_us = self.__int_time_low

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
        if binning_type == 0:
            # Restore default ABS pixel ramp magnitude if binning is disabled
            self._restore_abs_setting()
        else:          
            # Set new ABS pixel ramp magnitude & verify for binning mode
            newValue = 0x1f
            for reg in self.absRegisterSetting.keys():
                self.cam.tcpInterface.transceive(Command.create("writeRegister", {"address": reg, "value": newValue}))
                updatedRegValue = self.cam.tcpInterface.transceive(Command.create("readRegister", {"address": reg})).data
                if newValue != updatedRegValue:
                    raise ValueError(
                        f"ABS register mismatch at address 0x{reg:02X}: expected 0x{newValue:02X}, got 0x{updatedRegValue:02X}"
                    )

        # Try setbinning() and if it fails, revert ABS pixel ramp magnitude to default
        try:
            self.cam.tcpInterface.transceive(
                Command.create("setBinning", np.byte(binning_type))
            )
        except Exception as e:
            log.error(f"setBinning failed: {e}. Reverting ABS register to default.")
            self._restore_abs_setting()
            raise ValueError(f"setBinning failed: {e}. Reverted ABS register to default.")

    def set_dll_step(self, step: int = 0):
        log.info(f"Setting DLL step: {step}")
        self.cam.tcpInterface.transceive(Command.create("setDllStep", step))

    def set_minimal_amplitude(self, minimum: int):
        """Set minimal amplitude needed to be considered a valid distance estimation."""
        log.info(f"Setting minimum amplitude: {minimum}")
        self.cam.tcpInterface.transceive(Command.create("setMinAmplitude", minimum))
        self.minAmplitude = minimum

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

    def set_flex_mod_freq(self, frequency_mhz: int|float, delay = 0.1):
        self._clear_dll_settings() # Will be implemented in fw in the next release
        cmd = Command.create("setFlexModFreq", int(frequency_mhz*1E6))
        log.info(f"Setting flex modulation frequency: {frequency_mhz*1E6} Hz")
        self.cam.tcpInterface.transceive(cmd)
        time.sleep(delay)
        self.flexMod = True
        self.flexModFreq_MHz = frequency_mhz

    def set_modulation(self, frequency_mhz: float, channel=0):
        """Set the modulation frequency and channel for the TOFcam."""
        self._restore_dll_settings()
        
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
        self.flexMod = False

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

    def set_illuminator_segments(self, segment_1_on: bool = True, segment_2_on: bool = True, segment_3_on: bool = True,
                                 segment_4_on: bool = True, segment_2_to_4: bool = True):
        """Set the illuminator segments for the camera."""
        log.info(f"Setting illuminator segments: ("
                 f"1:{'ON' if segment_1_on else 'OFF'}, 2:{'ON' if segment_2_on else 'OFF'}, "
                 f"3:{'ON' if segment_3_on else 'OFF'}, 4:{'ON' if segment_4_on else 'OFF'}, "
                 f"2-4:{'ON' if segment_2_to_4 else 'OFF'})")
        set_illuminator_cmd = Command.create(
            "setIlluminatorSegments",
            {
                "segment1": segment_1_on,
                "segment2": segment_2_on,
                "segment3": segment_3_on,
                "segment4": segment_4_on,
                # Control segments 2, 3, and 4 (R100=0R needs to be assembled)
                "segment_2_to_4": segment_2_to_4,
            },
        )
        log.info(f"Command data: {set_illuminator_cmd.dataToBytes()}")
        log.info(f"Command: {set_illuminator_cmd.toBytes()}")
        self.cam.tcpInterface.transceive(set_illuminator_cmd)

    def get_integration_time(self, ) -> list[dict]:
        """Get the integration time(grayscale & 3D) from the camera."""
        log.info(f"Reading integration time")
        return self.cam.tcpInterface.transceive(Command.create("getIntegrationTime")).data


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

    def get_calibration_data(self, ) -> list[dict]:
        """Get the calibration data(calibrated modulation freq., temperature, atan offset) from the camera."""
        log.info(f"Reading calibration data")
        calibration_data = self.cam.tcpInterface.transceive(Command.create("getCalibrationData")).data
        return calibration_data
    
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























































































































































































































