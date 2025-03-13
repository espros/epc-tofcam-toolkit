import struct 
from sys import platform
import ctypes
import importlib.resources
import numpy as np
from enum import Enum

class CrcMode(Enum):
    CRC32_UINT8 = 1
    CRC32_UINT8_LIB = 2
    CRC32_STM32 = 3

class Crc:
    def __init__(self, mode: CrcMode = CrcMode.CRC32_UINT8,
                       polynom=0x04C11DB7, 
                       initvalue=0xFFFFFFFF, 
                       xorout=0x00000000, 
                       revout=False):
        self.polynom = polynom
        self.initvalue = initvalue
        self.revout = revout
        self.xorout = xorout
        self.mode = mode

        if mode == CrcMode.CRC32_UINT8_LIB:
            self.useLib = self.__loadLib()

    def __loadLib(self):
        try:
            if platform == 'linux':
                binaryPath = importlib.resources.files('epc.tofCam_lib.bin').joinpath('CrcCalc_linux.so')
                self.lib = ctypes.cdll.LoadLibrary(str(binaryPath))
            elif platform == 'win32':
                binaryPath = importlib.resources.files('epc.tofCam_lib.bin').joinpath('CrcCalc.dll')
                self.lib = ctypes.windll.LoadLibrary(str(binaryPath))
            elif platform == 'darwin':
                binaryPath = importlib.resources.files('epc.tofCam_lib.bin').joinpath('CrcCalc_darwin.a')
                self.lib = ctypes.cdll.LoadLibrary(str(binaryPath))
            else:
                raise Exception('Platform not supported')
            return True
        except Exception as e:
                print(e, 'no lib used')
                return False


    def __calcCrc32_python(self, crc, data):

        if(self.mode == CrcMode.CRC32_STM32):
            # this shift is done to make it compatible to the STM32 hardware CRC
            crc = np.uint32(crc^np.uint32(data << 24))
            bitRange = 8
        else:
            crc = crc ^ data
            bitRange = 32

        for _ in range(bitRange):
            if crc & 0x80000000:
                crc = ((crc << 1) & 0xFFFFFFFF) ^ self.polynom
            else:
                crc = (crc << 1) & 0xFFFFFFFF
        return crc
    
    def __calcCrc32Uin8_python(self, data: bytearray):
        crc = self.initvalue
        for i in range(len(data)):
            crc = self.__calcCrc32_python(crc, data[i])
            crc = crc ^ self.xorout
        return crc
    
    def __calcCrc32Uint8_lib(self, data: bytearray):
        self.lib.calcCrc32_32.restype=ctypes.c_uint32
        carray = (ctypes.c_uint8*len(data)).from_buffer(data)

        return self.lib.calcCrc32_32(carray,len(data),ctypes.c_uint32(self.polynom))

    def calculate(self, data: bytearray) -> bytearray:
        crc = bytearray([])
        match self.mode:
            case CrcMode.CRC32_UINT8:
                crc = self.__calcCrc32Uin8_python(data)
            case CrcMode.CRC32_UINT8_LIB:
                crc = self.__calcCrc32Uint8_lib(bytearray(data))
            case CrcMode.CRC32_STM32:
                crc = self.__calcCrc32Uin8_python(data)
        
        if self.revout:
            crc = struct.unpack('>I', struct.pack('<I', crc))[0]
        
        return crc

    def verify(self, data: bytearray, crc: bytearray):
        crc_calc = self.calculate(data)
        return crc_calc == struct.unpack('<I', bytearray(crc))[0]