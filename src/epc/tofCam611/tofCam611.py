import time
import struct
import logging
import numpy as np
from typing import Optional
from epc.tofCam_lib.tofCam import TOFcam, TOF_Settings_Controller, Dev_Infos_Controller
from epc.tofCam_lib.crc import Crc, CrcMode
from epc.tofCam_lib.transformations_3d import depth_to_3d
from epc.tofCam611.communicationType import communicationType as ComType
from epc.tofCam611.commandList import commandList as CommandList
from epc.tofCam611.serialInterface import SerialInterface

MAX_INTEGRATION_TIME = 2**16-1
EPC911_PAGE_SIZE = 0x20
ERROR_MIN_AMPLITUDE = 16001000
DEVICE_TOFFRAME = 1
DEVICE_TOFRANGE = 0
DEFAULT_MAX_DEPTH = 16000

log = logging.getLogger('TOFcam611')

# THIS IS A TEMPORARY WRAPPER AND IS INTENDEN TO BE REPLACED AT SOME POINT BY A STANDARD INTERFACE FOR ALL TOF CAMERAS
class InterfaceWrapper:
    def __init__(self, port: Optional[str]=None) -> None:
        self.com = SerialInterface(port, timeout=1)
        self.crc = Crc(mode=CrcMode.CRC32_STM32, revout=False)
        self.__capture_mode = 0
        self.__answer_table = {
            ComType.DATA_INTEGRATION_TIME: 10,
            ComType.DATA_PRODUCTION_INFO: 10,
            ComType.DATA_REGISTER: 10,
            ComType.DATA_CHIP_INFORMATION: 12,
            ComType.DATA_IDENTIFICATION: 12,
            ComType.DATA_FIRMWARE_RELEASE: 12,
            ComType.DATA_TEMPERATURE: 10,
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
        if len(tmp) != LEN_BYTES:
            raise Exception(f"Wrong number of bytes received! expected {LEN_BYTES}, got {len(tmp)}")
        if not self.crc.verify(tmp[:-4], tmp[-4:]):
            raise Exception("CRC not valid!!")
        if tmp[1] != ComType.DATA_ACK:
            raise Exception("Got wrong type!:{:02x}".format(tmp[1]))
        return True
    
    def getAnswer(self, typeId, length):
        tmp=self.com.read(length)
        
        if len(tmp) != length:
            raise Exception("Wrong number of bytes received!!, expected {:02d}, got {:02d}".format(length, len(tmp)))
        if not self.crc.verify(tmp[:-4], tmp[-4:]):
            raise Exception("CRC not valid!!")
        if tmp[1] == ComType.DATA_NACK:
            raise Exception("received NACK")
        if typeId != tmp[1]:
            raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))
        length= struct.unpack('<'+'H',tmp[2:4])[0]
        return tmp[4:4+length]
       
    def get_image_data(self, cmd_id: int, ret_id: int):
        self.tofWrite([cmd_id])
        tmp=self.com.read(4)
        total = bytes(tmp)
        length = struct.unpack('<'+'H',tmp[2:4])[0]
        tmp = self.com.read(length+4)
        total+=bytes(tmp)
        self.crc.verify(bytearray(total[:-4]), bytearray(total[-4:]))
        if ret_id != total[1]:
           raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(ret_id,tmp[1]))

        return [tmp[:-4],length]

    def transmit(self, cmd_id: int, arg=[]):
        arg.insert(0, cmd_id)
        self.tofWrite(arg)
        self.getAcknowledge()

    def transceive(self, cmd_id: int, response_id: int, arg=[]):
        arg.insert(0, cmd_id)
        self.tofWrite(arg)
        lengt = self.__get_answer_len(response_id)
        return self.getAnswer(response_id, lengt)


class TOFcam611_Settings(TOF_Settings_Controller):
    def __init__(self, interface: InterfaceWrapper, device_type: int) -> None:
        self.interface = interface
        self._min_amplitude = 0
        self.__mod_freq = 0
        self._mod_channel = 0
        self._device_type = device_type
        self.maxDepth = DEFAULT_MAX_DEPTH
        self.roi = self.get_roi()
        self.resolution = (self.roi[2], self.roi[3])

    def get_roi(self):
        if self._device_type == DEVICE_TOFFRAME:
            return (0, 0, 8, 8)
        elif self._device_type == DEVICE_TOFRANGE:
            return (0, 0, 1, 1)

    def set_minimal_amplitude(self, amplitude: int):
        log.info(f"set minimal amplitude to {amplitude}")
        self._min_amplitude = amplitude

    def set_integration_time(self, int_time_us: int):
        if 0 > int_time_us > MAX_INTEGRATION_TIME:
            raise ValueError(f"integration time must be between 0 and {MAX_INTEGRATION_TIME} us")
        log.info(f"set integration time to {int_time_us} us")
        self.interface.transmit(CommandList.COMMAND_SET_INTEGRATION_TIME_3D, [0 , int_time_us &0xff, (int_time_us>>8)&0xff])

    def get_integration_time(self):
        response = self.interface.transceive(CommandList.COMMAND_GET_INTEGRATION_TIME_3D, ComType.DATA_INTEGRATION_TIME)
        return response[0]+response[1]*0x100
    
    def set_dll_steps(self, step: int = 0):
        log.info(f"set dll step to {step}")
        self.interface.transmit(CommandList.COMMAND_SET_DLL_STEP, [step])

    def set_modulation(self, frequency_mhz: float, channel=0):
        if 10 == frequency_mhz:
            self.__mod_freq = 0
        elif 20 == frequency_mhz:
            self.__mod_freq = 1
        else:
            raise ValueError(f"frequency {frequency_mhz} not supported")
        log.info(f"set modulation frequency to {frequency_mhz} MHz")
        self.interface.transmit(CommandList.COMMAND_SET_MODULATION_FREQUENCY, [self.__mod_freq, self._mod_channel])

    def get_modulation_frequencies(self) -> list[float]:
        if self._device_type == DEVICE_TOFFRAME:
            return [20]
        elif self._device_type == DEVICE_TOFRANGE:
            return [10]
        else:
            raise ValueError(f"device type {self._device_type} not supported")
        
    def get_modulation_channels(self) -> list[int]:
        return []
    
    def set_temporal_filter(self, treshold, factor):
        log.info(f"set temporal filter to treshold {treshold} and factor {factor}")
        self.interface.transmit(CommandList.COMMAND_SET_FILTER, [treshold &0xff, (treshold>>8)&0xff, factor&0xff,  (factor>>8)&0xff])

    def write_calibration_data(self, data: bytes):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'write_calibration_data' jet")
    
    def update_firmware(self, data: bytes):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'update_firmware' jet")

class TOFcam611_Device(Dev_Infos_Controller):
    def __init__(self, interface: InterfaceWrapper) -> None:
        self.interface = interface
    
    def __get_register_page_and_offset(self, reg_addr: int) -> tuple[int, int]:
        page = reg_addr // EPC911_PAGE_SIZE
        offset = reg_addr % EPC911_PAGE_SIZE
        return (page, offset)
    
    def get_chip_infos(self) -> tuple[int, int]:
        """returns (chipType, version)"""
        response = self.interface.transceive(CommandList.COMMAND_GET_CHIP_INFORMATION, ComType.DATA_CHIP_INFORMATION)
        data = list(struct.unpack('<'+'H'*2, response))
        return (data[0], data[1]) # chipType, version
    
    def get_chip_temperature(self) -> float:
        """returns the chip temperature in °C"""
        response = self.interface.transceive(CommandList.COMMAND_GET_TEMPERATURE, ComType.DATA_TEMPERATURE)
        temperature=struct.unpack('<'+'h', response)[0]
        return float(temperature)/100.0

    def get_device_ids(self) -> tuple[int, int, int]:
        """returns a tuple with (chipType, device, version)"""
        response = self.interface.transceive(CommandList.COMMAND_IDENTIFY, ComType.DATA_IDENTIFICATION)
        answer =struct.unpack('<'+'BBBB',response)
        return (answer[2], answer[1], answer[0]) # chipType, device, version
    
    def get_device_id(self) -> any:
        chip_type, device, version = self.get_device_ids()
        return f'ChipType: {chip_type}, Device: {device}, Version: {version}'
    
    def get_fw_version(self) -> str:
        """returns the firmware version as string in format 'major.minor'"""
        response = self.interface.transceive(CommandList.COMMAND_GET_FIRMWARE_RELEASE, ComType.DATA_FIRMWARE_RELEASE)
        fwRelease=struct.unpack('<'+'I',response)[0]
        major = fwRelease>>16
        minor = fwRelease&0xffff
        return f'{major}.{minor}'

    def write_register(self, reg_addr: int, value: int) -> None:
        page, offset = self.__get_register_page_and_offset(reg_addr)
        log.info(f"write register at page 0x{hex(page)} and offset 0x{hex(offset)} with value {hex(value)}")
        self.interface.transmit(CommandList.COMMAND_WRITE_REGISTER, [offset, page, value])

    def read_register(self, reg_addr: int) -> int:
        page, offset = self.__get_register_page_and_offset(reg_addr)
        log.info(f"read register at page 0x{hex(page)} and offset 0x{hex(offset)}")
        response = self.interface.transceive(CommandList.COMMAND_READ_REGISTER, ComType.DATA_REGISTER, [offset, page])
        return int(response[0])

    def get_production_date(self):
        """returns the production date as tuple (year, week)"""
        response = self.interface.transceive(CommandList.COMMAND_GET_PRODUCTION_INFO, ComType.DATA_PRODUCTION_INFO)
        week= response[1]
        year= response[0]
        return (year, week)
    
    def get_error(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_error' jet")

    def set_power(self, enable=True):
        log.info(f"set power to {enable}")
        # self.interface.transmit(CommandList.COMMAND_SET_POWER, [int(enable)])
        self.interface.tofWrite([CommandList.COMMAND_SET_POWER, int(enable)])
        time.sleep(1)
        self.interface.getAcknowledge()

class TOFcam611(TOFcam):
    """creates a TOFcam611 object and connects the camera to the given port. 
    This class can also be used for the TOFrange since they share the same communication protocol.

    If no port is specified, the TOFcam611 object will try to find the correct port automatically.

    The TOFcam611 object holds two attributes for settings and device information.

    - settings: can be used to control the settings of the camera
    - device: can be used to get information about the camera
    """
    def __init__(self, port: Optional[str]=None) -> None:
        self.interface = InterfaceWrapper(port)
        self.device = TOFcam611_Device(self.interface)
        device_type = self.device.get_device_ids()[1]
        self.settings = TOFcam611_Settings(self.interface, device_type)
        super().__init__(self.settings, self.device)

    def __del__(self):
        if self.interface.com is not None:
            self.interface.com.close()

    def initialize(self):
        """initialize the camera with default values and set power to on"""
        log.info("initialize TOFcam611")
        self.device.set_power(True)
        self.settings.set_integration_time(50)

    def get_grayscale_image(self):
        """!!! ATTENTION !!!\n
            TOFcam611 doesn't implement capturing of grayscale images. Therefore the grayscale image is estimaged as the sum of 4 DCS images.
            returns the grayscale image as 2d numpy array
        """
        dcs = self.get_dcs_images()
        return dcs.sum(axis=0)
    
    def get_amplitude_image(self):
        """returns the amplitude image as 2d numpy array"""
        data, length = self.interface.get_image_data(CommandList.COMMAND_GET_AMPLITUDE, ComType.DATA_AMPLITUDE)
        if length == 4:
            amplRaw =np.array((struct.unpack('<'+'I',data)))
        else:
            amplRaw=np.array((struct.unpack('<'+'I'*int(length/4),data)))
        amplitude = np.reshape(amplRaw, self.settings.resolution)
        return amplitude

    def get_distance_image(self):
        """returns the distance image as 2d numpy array"""
        dist, amp =  self.get_distance_and_amplitude_image()
        dist[amp < self.settings._min_amplitude] = ERROR_MIN_AMPLITUDE
        return dist   
    
    def get_dcs_images(self) -> np.ndarray:
        """returns 4 DCS images as a numpy array of shape (4, 8, 8)"""
        data, length = self.interface.get_image_data(CommandList.COMMAND_GET_DCS, ComType.DATA_DCS)
        if length == 12:
            dcsRaw=np.array((struct.unpack('<'+'i'*4,data)))
            dcs=dcsRaw
        elif length == 8:
            dcsRaw=np.array((struct.unpack('<'+'h'*4,data)))
            dcs=dcsRaw
        else:
            dcsRaw=np.array((struct.unpack('<'+'h'*int(length/2),data)))
            dcs = np.reshape(dcsRaw,(4,*self.settings.resolution))
        return dcs

    def get_distance_and_amplitude_image(self):
        """returns a tuple of (distance, amplitude) images as 2d numpy arrays"""
        data, lengt = self.interface.get_image_data(CommandList.COMMAND_GET_DISTANCE_AMPLITUDE, ComType.DATA_DISTANCE_AMPLITUDE)
        if lengt == 8:
            distRaw =np.array((struct.unpack('<'+'I',data[:-4])))
            amplRaw =np.array((struct.unpack('<'+'I',data[4:])))
        else:
            distRaw   = np.array((struct.unpack('<'+'I'*(lengt//8),data[:lengt//2])))
            amplRaw   = np.array((struct.unpack('<'+'I'*(lengt//8),data[lengt//2:])))
        distance  = np.reshape(distRaw, self.settings.resolution)
        amplitude = np.reshape(amplRaw, self.settings.resolution)
        return distance/10, amplitude


    def get_point_cloud(self):
        depth = self.get_distance_image()
        depth  = depth.astype(np.float32)
        depth[depth >= self.settings.maxDepth] = np.nan

        # calculate point cloud from the depth image
        roi = self.settings.get_roi()
        points = 1E-3 * depth_to_3d(np.fliplr(depth), resolution=(self.settings.resolution), focalLengh=40) # focul lengh in px (0.8 mm)
        points = np.transpose(points, (1, 2, 0))
        points = points.reshape(-1, 3)
        return points