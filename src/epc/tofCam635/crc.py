"""
* Copyright (C) 2019 Espros Photonics Corporation
*
* Open Source Software used:
* - numpy: Copyright © 2005-2019, NumPy Developers.
"""

import numpy as np
from sys import platform
import ctypes
import struct
import sys
import time
import os


class Crc():
  def __init__(self):
    self.initValue =np.uint32(0xFFFFFFFF)
    self.POLYNOM  = np.uint32(0x04C11DB7)
    os.environ['PATH'] = os.path.dirname(__file__) + ';' + os.environ['PATH']

    #self._use_lib = False
    # try:
    #     if platform == 'linux':
    #         self.lib = ctypes.cdll.LoadLibrary('CrcCalc.so')
    #     elif platform == 'win32':
    #         self.lib = ctypes.windll.LoadLibrary('CrcCalc.dll')
    #     self._use_lib=True
    # except:
    #     print('no lib used')
    #     self._use_lib=False
    #self.lib = ctypes.windll.LoadLibrary('H:\635\SW_TofCam635_Communication_lib\SW_TofCam635_Communication_lib\CrcCalc.dll')
    self._use_lib=True
    self.lib = ctypes.windll.LoadLibrary(r'..\SW_TofCam635_Communication_lib\CrcCalc.dll')
   




  def calcCrc32(self,data, size):
    """
    calculates the 4 byte checksum from data
    @param data data to calculate checksum of
    @param size length of data without checksum from serial

    @return checksum
    """

    self.lib.calcCrc32_32.restype=ctypes.c_uint32
    carray = (ctypes.c_uint8*len(data)).from_buffer(data)

    return self.lib.calcCrc32_32(carray,len(data),ctypes.c_uint32(self.POLYNOM))

  def getCrc(self,data):
    return struct.unpack('<'+'I',data[-4:])[0]

  def isCrcValid(self,data):
    gotCrc=self.getCrc(data[-4:])
    if sys.version_info <= (3, 0):
      tmp =[]
      for i in data:
        tmp.append(ord(i))
      data = tmp
    calcCrc = self.calcCrc32(bytearray(data[:-4]),len(data)-4)
    #print('{:x}={:x}'.format(calcCrc,gotCrc))
    if(calcCrc==gotCrc):
      return True
    else:
      raise Exception("CRC not valid!! Received: 0x{:08x} !=\n                         Calculated: 0x{:08x} ".format(gotCrc,calcCrc))



