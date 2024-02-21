import struct 
from sys import platform
import ctypes
import pkg_resources
import numpy as np

class Crc:
    def __init__(self, polynom=0x04C11DB7, 
                       initvalue=0xFFFFFFFF, 
                       xorout=0x00000000, 
                       revout=False, 
                       useLib = False,
                       stmMode = False):
        self.polynom = polynom
        self.initvalue = initvalue
        self.revout = revout
        self.xorout = xorout
        self.useLib = useLib
        self.stmMode = stmMode

        if self.useLib:
            self.useLib = self.__loadLib()

    def __loadLib(self):
        try:
            if platform == 'linux':
                binaryPath = pkg_resources.resource_filename('epc', 'tofCam_lib/bin/CrcCalc_linux.so')
                self.lib = ctypes.cdll.LoadLibrary(binaryPath)
            elif platform == 'win32':
                binaryPath = pkg_resources.resource_filename('epc', 'tofCam_lib/bin/CrcCalc.dll')
                self.lib = ctypes.windll.LoadLibrary(binaryPath)
            return True
        except Exception as e:
                print(e, 'no lib used')
                return False


    def __calcCrc32_python(self, crc: int, data: int):

        if(self.stmMode):
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

    
    def calcCrc32Uint8(self, data: bytearray):

        if(self.stmMode): # for tofCam611
            crc = self.__calcCrc32Uin8_python(data)
        else:
            if self.useLib:
                crc = self.__calcCrc32Uint8_lib(data)
            else:
                crc = self.__calcCrc32Uin8_python(data)
        if self.revout:
            crc = struct.unpack('>I', struct.pack('<I', crc))[0]
        return crc

    def verify(self, data: bytearray):
        crc = self.calcCrc32Uint8(data[:-4])
        return crc == struct.unpack('<I', data[-4:])[0]