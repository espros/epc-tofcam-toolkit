import struct
import logging
import time
from threading import Lock
import numpy as np
from typing import Optional
from epc.tofCam_lib.tofCam import TOFcam, TOF_Settings_Controller, Dev_Infos_Controller
from epc.tofCam_lib.crc import Crc, CrcMode
from epc.tofCam635.communication import Type as ComType
from epc.tofCam635.communication import Data as Data_Type
from epc.tofCam_lib.transformations_3d import Lense_Projection

from epc.tofCam635.communication import SerialInterface
from epc.tofCam635.communication import CommandList
from epc.tofCam635.tofcam635Header import TofCam635Header

DEFAULT_ROI = (0, 0, 160, 60)
MAX_DIST_INT_TIME = 2**16-1
DEFAULT_MAX_DEPTH = 16000

log = logging.getLogger('TOFcam635')

# THIS IS A TEMPORARY WRAPPER AND IS INTENDEN TO BE REPLACED AT SOME POINT BY A STANDARD INTERFACE FOR ALL TOF CAMERAS
class InterfaceWrapper:
    def __init__(self, port: Optional[str]=None) -> None:
        self.com = SerialInterface(port)
        self.crc = Crc(mode=CrcMode.CRC32_UINT8_LIB, revout=False)
        self.header = TofCam635Header()
        self.__lock = Lock()
        self.__answer_table = {
            ComType.DATA_CHIP_INFORMATION: 12,
            ComType.DATA_CALIBRATION_INFO: 22,
            ComType.DATA_REGISTER: 9,
            ComType.DATA_FIRMWARE_RELEASE: 12,
            ComType.DATA_TEMPERATURE: 10,
            ComType.DATA_IDENTIFICATION: 12
        }

    def __get_answer_len(self, ret_type: int) -> int:
        try:
            return self.__answer_table[ret_type]
        except KeyError:
            raise ValueError(f"return type '{ret_type}' not supported")

    def tofWrite(self, values) -> None:
        if type(values)!=list:
            values = [values]
        values += [0] * (9 - len(values)) #fill up to size 9 with zeros
        a=[0xf5]*14
        a[1:10]=values

        crc = np.array(self.crc.calculate(bytearray(a[:10])))
        
        a[10] = crc & 0xff
        a[11] = (crc>>8) & 0xff
        a[12] = (crc>>16) & 0xff
        a[13] = (crc>>24) & 0xff

        self.com.write(a)

    def getAcknowledge(self):
        """
        ask for acknowledge
        @return True if acknowledge was received otherwise return False
        """
        LEN_BYTES = 8
        tmp=self.com.read(LEN_BYTES)
        if not self.crc.verify(tmp[:-4], tmp[-4:]):
            raise Exception("CRC not valid!!")
        if tmp[1] != ComType.DATA_ACK:
            raise Exception("Got wrong type!:{:02x}".format(tmp[1]))
        if len(tmp) != LEN_BYTES:
            raise Exception("Not enought bytes!")
        return True
    
    def getAnswer(self, typeId, length):
        tmp=self.com.read(length)
        
        if not self.crc.verify(tmp[:-4], tmp[-4:]):
            raise Exception("CRC not valid!!")
        if len(tmp) != length:
            raise Exception("Not enough bytes!!, expected {:02d}, got {:02d}".format(length, len(tmp)))
        if typeId != tmp[1]:
            raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))
        if typeId == ComType.DATA_NACK:
            raise Exception("NACK")
        length= struct.unpack('<'+'H',tmp[2:4])[0]
        return tmp[4:4+length]
    
    def get_image_data(self, cmd_id: int, type_id: int, arg=[]):
        self.__lock.acquire()
        arg.insert(0, cmd_id)
        self.tofWrite(arg)
        tmp=self.com.read(Data_Type.SIZE_HEADER)
        total = bytes(tmp)
        length = struct.unpack('<'+'H',tmp[Data_Type.INDEX_LENGTH:Data_Type.INDEX_LENGTH + Data_Type.SIZE_LENGTH])[0]
        tmp = self.com.read(length+4)
        self.__lock.release()
        total+=bytes(tmp)
        if not self.crc.verify(bytearray(total[:-4]), bytearray(total[-4:])):
            raise Exception("CRC not valid!!")
        if type_id != total[1]:
            raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(type_id,tmp[1]))

        self.header.extractData(tmp)

        # Remove header at beginning and checksum at the end
        return [tmp[self.header.getHeaderSize():-4],length]

    def transmit(self, cmd_id: int, arg=[]):
        self.__lock.acquire()
        arg.insert(0, cmd_id)
        self.tofWrite(arg)
        self.getAcknowledge()
        self.__lock.release()

    def transceive(self, cmd_id: int, response_id: int, arg=[]):
        self.__lock.acquire()
        arg.insert(0, cmd_id)
        self.tofWrite(arg)
        len = self.__get_answer_len(response_id)
        answer = self.getAnswer(response_id, len)
        self.__lock.release()
        return answer


class TOFcam635_Settings(TOF_Settings_Controller):
    """This class is used to control the settings of the TOFcam635 camera.
    """
    def __init__(self, interface: InterfaceWrapper) -> None:
        super().__init__()
        self.roi = DEFAULT_ROI
        self.resolution = (self.roi[2] - self.roi[0], self.roi[3] - self.roi[1])
        self.interface = interface
        self._capture_mode = 0
        self.max_depth = DEFAULT_MAX_DEPTH
        self.lensProjection = Lense_Projection.from_lense_calibration(lensType='Wide Field', width=self.resolution[0], height=self.resolution[1])


    def set_roi(self, roi: tuple[int, int, int, int]) -> None:
        """ Set the region of interest (ROI) for the camera.
            The ROI is set to the nearest multiple of 4
            
            returns: the set ROI"""
        roi = tuple(round(x/4)*4 for x in roi)
        x0, y0, x1, y1 = roi
        log.info(f"Setting ROI to {x0}, {y0}, {x1}, {y1}")
        self.interface.transmit(CommandList.COMMAND_SET_ROI, [x0&0xff, (x0>>8)&0xff,  y0&0xff, (y0>>8)&0xff,  x1&0xff, (x1>>8)&0xff,  y1&0xff, (y1>>8)&0xff])
        self.resolution = (x1-x0, y1-y0)
        self.roi = roi
        return self.roi

    def get_roi(self) -> tuple[int, int, int, int]:
        """Returns the current region of interest (ROI) of the camera.

        Returns:
            tuple[int, int, int, int]: x0, y0, x1, y1
        """
        return self.roi

    def set_capture_mode(self, mode: int) -> None:
        """set the capture mode for next image aquisition

        Args:
            mode (int): 0: single measurement, 1: pipelined measurement, 2: streaming mode
        """
        self._capture_mode = mode

    def set_minimal_amplitude(self, amplitude: int):
        """set the minimal amplitude for valid distance calculation

        Args:
            amplitude (int): minimal amplitude [ADC]
        """
        log.info(f"Setting minimal amplitude to {amplitude}")
        for i in range(5):
            self.interface.transmit(CommandList.COMMAND_SET_AMPLITUDE_LIMIT, [i, amplitude&0xff, (amplitude>>8)&0xff])

    def set_dll_steps(self, step: int = 0):
        log.info(f"Setting DLL step to {step}")
        self.interface.transmit(CommandList.COMMAND_SET_DLL_STEP, [step])

    def set_integration_time(self, int_time_us: int):
        """set integration time for standard mode (e.g. hdr off)
        """
        log.info(f"Setting integration time to {int_time_us}")
        return self.set_integration_time_hdr(int_time_us, 0)
    
    def set_integration_time_grayscale(self, int_time_us: int):
        """set integration time for grayscale acquisition
        """
        log.info(f"Setting grayscale integration time to {int_time_us}")
        if 0 > int_time_us > MAX_DIST_INT_TIME:
            raise ValueError(f"Integration time '{int_time_us}' is too high")
        self.interface.transmit(CommandList.COMMAND_SET_INTEGRATION_TIME_GRAYSCALE, [int_time_us&0xff, (int_time_us>>8)&0xff]) 

    def set_integration_time_hdr(self, index: int, int_time_us: int) -> None:
        """set integration time for HDR mode
        """
        log.info(f"Setting HDR integration time {index} to {int_time_us}")
        if 0 > int_time_us > MAX_DIST_INT_TIME:
            raise ValueError(f"Integration time '{int_time_us}' is too high")
        self.interface.transmit(CommandList.COMMAND_SET_INT_TIME_DIST, [index, int_time_us&0xff, (int_time_us>>8)&0xff])

    def set_modulation(self, frequency_mhz: float, channel=0):
        if frequency_mhz == 10:
            frequency_code = 0
        elif frequency_mhz == 20:
            frequency_code = 1
        else:
            raise ValueError(f"Invalid modulation frequency '{frequency_mhz}'")
        log.info(f'Setting modulation: frequency={frequency_mhz}MHz, channel={channel}')
        self.interface.transmit(CommandList.COMMAND_SET_MODULATION_FREQUENCY, [frequency_code])
        self.interface.transmit(CommandList.COMMAND_SET_MOD_CHANNEL, [0, channel])

    def get_modulation_frequencies(self) -> list[float]:
        return [10.0, 20.0]
    
    def get_modulation_channels(self) -> list[int]:
        return list(range(16))
    
    def set_binning(self, enable: bool) -> None:
        log.info(f"Setting binning to {enable}")
        self.interface.transmit(CommandList.COMMAND_SET_BINNING, [int(enable)])

    def set_operation_mode(self, mode: int) -> None:
        log.info(f"Setting operation mode to {mode}")
        self.interface.transmit(CommandList.COMMAND_SET_OPERATION_MODE, [mode])


    def set_hdr(self, mode='off') -> None:
        """select hdr mode

        Args:
            mode (str): 'off', 'spatial' or 'temporal'. Defaults to 'off'.
        """
        hdr_mode = 0
        if mode == 'off':
            hdr_mode = 0
        elif mode == 'spatial':
            hdr_mode = 1
        elif mode == 'temporal':
            hdr_mode = 2
        else:
            raise ValueError(f"Invalid hdr mode '{mode}'")
        
        log.info(f"Setting HDR mode to {mode}")
        self.interface.transmit(CommandList.COMMAND_SET_HDR, [hdr_mode])

    def set_median_filter(self, enable: bool) -> None:
        log.info(f"Setting median filter to {enable}")
        self.interface.transmit(CommandList.COMMAND_SET_MEDIAN_FILTER, [int(enable)])

    def set_average_filter(self, enable: bool) -> None:
        log.info(f"Setting average filter to {enable}")
        self.interface.transmit(CommandList.COMMAND_SET_AVERAGE_FILTER, [int(enable)])

    def set_temporal_filter(self, enable: bool, threshold: int, factor: int) -> None:
        log.info(f"Setting temporal filter to {enable} with threshold {threshold} and factor {factor}")
        if enable:
            self.interface.transmit(CommandList.COMMAND_SET_TEMPORAL_FILTER_WFOV, [threshold & 0xff, (threshold>>8) & 0xff,factor & 0xff, (factor>>8) & 0xff])
        else:
            self.interface.transmit(CommandList.COMMAND_SET_TEMPORAL_FILTER_WFOV, [0, 0, 0, 0])

    def set_edge_filter(self, enable: bool, threshold: int) -> None:
        log.info(f"Setting edge filter to {enable} with threshold {threshold}")
        if enable:
            self.interface.transmit(CommandList.COMMAND_SET_EDGE_FILTER, [threshold & 0xff, (threshold>>8) & 0xff])
        else:
            self.interface.transmit(CommandList.COMMAND_SET_EDGE_FILTER, [0, 0])

    def set_interference_detection(self, enable: bool, useLast=False, limit=500):
        log.info(f"Setting interference detection to {enable} with useLast={useLast} and limit={limit}")
        self.interface.transmit(CommandList.COMMAND_SET_INTERFERENCE_DETECTION, [int(enable), int(useLast), limit & 0xff, (limit>>8) & 0xff])


class TOFcam635_Device(Dev_Infos_Controller):
    """This class is used to control the device information of the TOFcam635 camera.
    """
    def __init__(self, interface: InterfaceWrapper) -> None:
        super().__init__()
        self.interface = interface

    def get_chip_infos(self) -> tuple[int, int]:
        """returns chip information

        Returns:
            tuple[int, int]: chipId, waferId
        """
        data = self.interface.transceive(CommandList.COMMAND_GET_CHIP_INFORMATION, ComType.DATA_CHIP_INFORMATION)
        response=list(struct.unpack('<'+'H'*2,data))
        return (response[0], response[1])
    
    def get_fw_version(self) -> str:
        """returns firmware version as string"""
        data = self.interface.transceive(CommandList.COMMAND_GET_FIRMWARE_RELEASE, ComType.DATA_FIRMWARE_RELEASE)
        fwRelease = struct.unpack('<'+'I',data)[0]
        return str(float(fwRelease>>16) + float(fwRelease&0xffff)/100)
    
    def get_chip_temperature(self) -> float:
        """returns chip temperature in degree Celsius"""
        data = self.interface.transceive(CommandList.COMMAND_GET_TEMPERATURE, ComType.DATA_TEMPERATURE)
        centi_temperature=struct.unpack('<'+'h',data)[0]
        temperature = float(centi_temperature)/100
        return temperature
    
    def get_device_ids(self) -> tuple[int, int, int, int]:
        """return device ids
        
        Returns:
            tuple[int, int, int, int]: hwVersion, deviceType, chipType, oPmode
        """
        data = self.interface.transceive(CommandList.COMMAND_IDENTIFY, ComType.DATA_IDENTIFICATION)
        response = struct.unpack('<'+'I',data)[0]
        oPmode=((response&0xff000000)>>24)
        chipType=((response&0x00ff0000)>>16)
        deviceType=((response&0x0000ff00)>>8)
        hwVersion=(response&0x000000ff)
        return (hwVersion, deviceType, chipType, oPmode)
    
    def get_device_id(self) -> any:
        op_mode, chip_type, device_type, hw_version = self.get_device_ids()
        return f'HW Version: {hw_version}, Device Type: {device_type}, Chip Type: {chip_type}, Operation Mode: {op_mode}'

    def write_register(self, reg_addr: int, value: int) -> None:
        """write a register of the epc635 camera chip. 
        """
        log.info(f"Writing register {reg_addr} with value {value}")
        self.interface.transmit(CommandList.COMMAND_WRITE_REGISTER, [reg_addr&0xff, value])

    def read_register(self, reg_addr: int) -> int:
        """read a register of the epc635 camera chip."""
        log.info(f"Reading register {reg_addr}")
        data = self.interface.transceive(CommandList.COMMAND_READ_REGISTER, ComType.DATA_REGISTER, [reg_addr&0xff])
        return int(data[0])
    
    def system_reset(self) -> None:
        log.warning("Resetting system")
        self.interface.transmit(CommandList.COMMAND_SYSTEM_RESET)

    def get_calibration_info(self):
        return self.interface.transceive(CommandList.COMMAND_GET_CALIBRATION_INFO, ComType.DATA_CALIBRATION_INFO)


class TOFcam635(TOFcam):
    """creates a TOFcam635 object and connects the camera to the given port. 

    If no port is specified, the camera will try to find the correct port automatically.

    The TOFcam635 object holds two attributes for settings and device information.

    - settings: can be used to control the settings of the camera
    - device: can be used to get information about the camera
    """
    def __init__(self, port: Optional[str]=None) -> None:
        self.interface = InterfaceWrapper(port)
        self.settings = TOFcam635_Settings(self.interface)
        self.device = TOFcam635_Device(self.interface)
        super().__init__(self.settings, self.device)

    def __del__(self):
        if hasattr(self, 'interface'):
            self.interface.com.close()

    def initialize(self):
        log.info('Initializing TOFcam635')
        self.settings.set_roi(self.settings.roi)
        self.settings.set_operation_mode(0)
        self.settings.set_hdr('off')
        self.settings.set_modulation(frequency_mhz=20, channel=0)
        self.settings.set_integration_time(125)
        self.settings.set_integration_time_grayscale(50)
        self.settings.set_minimal_amplitude(100)
        self.settings.set_median_filter(False)
        self.settings.set_average_filter(False)
        self.settings.set_edge_filter(False, 150)
        self.settings.set_temporal_filter(False, 150, 10)
        self.settings.set_interference_detection(False, False, 500)

    def get_calibration_data(self):
        pass

    def get_grayscale_image(self):
        """returns a grayscale image as a 2d numpy array
        """
        data, _ = self.interface.get_image_data(CommandList.COMMAND_GET_GRAYSCALE, ComType.DATA_GRAYSCALE, [self.settings._capture_mode])
        grayscale = np.frombuffer(data, dtype='b')
        grayscale = grayscale.reshape(self.settings.resolution[::-1]).astype('uint8')
        return grayscale
    
    def get_distance_image(self):
        """returns a distance image as a 2d numpy array"""
        data, _ = self.interface.get_image_data(CommandList.COMMAND_GET_DISTANCE, ComType.DATA_DISTANCE, [self.settings._capture_mode])
        distance_and_confidence =  np.frombuffer(data, dtype="h")
        distance = []
        confidence = []

        #Mask out distance and confidence
        for i in range(len(distance_and_confidence)):
            distance.append(distance_and_confidence[i] & 0x3FFF)
            confidence.append((distance_and_confidence[i] >> 14) & 0x03)

        distance = np.reshape(distance, self.settings.resolution[::-1])
        # confidence = np.reshape(confidence, self.settings.resolution[::-1])
        return distance
    
    def get_amplitude_image(self):
        """returns an amplitude image as a 2d numpy array"""
        _, amplitude = self.get_distance_and_amplitude_image()
        return amplitude
    
    def get_distance_and_amplitude_image(self):
        """returns a tuple of 2d arrays (distance, amplitude)"""
        data, _ = self.interface.get_image_data(CommandList.COMMAND_GET_DISTANCE_AMPLITUDE, ComType.DATA_DISTANCE_AMPLITUDE, [self.settings._capture_mode])
        distance_and_confidence =  np.frombuffer(data, dtype="h")
        dist_amp = []
        confidence = []

        #Mask out distance and amplitude
        for i in range(len(distance_and_confidence)):
            dist_amp.append(distance_and_confidence[i] & 0x3FFF)
            confidence.append((distance_and_confidence[i] >> 14) & 0x03)

        distance = np.reshape(dist_amp[::2], self.settings.resolution[::-1])
        amplitude = np.reshape(dist_amp[1::2], self.settings.resolution[::-1])
        # confidence = np.reshape(confidence, self.settings.resolution[::-1])

        return distance, amplitude
    
    def get_point_cloud(self):
        """returns point cloud information as numpy array of shape (n, 3) with x, y, z coordinates"""
        # capture depth image & corrections
        depth = self.get_distance_image()
        depth  = depth.astype(np.float32)
        depth[depth >= self.settings.max_depth] = np.nan

        # calculate point cloud from the depth image
        points = 1E-3 * self.settings.lensProjection.transformImage(np.fliplr(depth.T))
        points = np.transpose(points, (2, 1, 0))
        points = points.reshape(-1, 3)
        return points
    