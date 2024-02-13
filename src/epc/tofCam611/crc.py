
import numpy as np
import struct
import sys

class crc():
  def __init__(self):
    self.initValue =np.uint32(0xFFFFFFFF)
    self.POLYNOM  = np.uint32(0x04C11DB7)
    
  def calcCrc32(self,data, size):
    """
    calculates the 4 byte checksum from data
    @param data data to calculate checksum of
    @param size length of data without checksum from serial
    
    @return checksum
    """
    crc = np.copy(self.initValue)
    for i in range(size):
        #iterate over size of data
        crc = self.calcCrc32Uint8(crc, np.uint32(data[i]));
    return crc

    
  def calcCrc32Uint8(self,crc,data):
    """
    Calculates the checksum of 4 bytes
    
    @param crc actual checksum before byte n
    @param data[n]
    
    @return checksum after byte n
    """

    #This shift is done to make it compatible to the STM32 hardware CRC
    crc = np.uint32(crc^np.uint32(data << 24))
    for i in range(8):
      if (crc & 0x80000000):
        crc = np.uint32(np.uint32(crc << 1)^self.POLYNOM)
      else:
        crc = np.uint32(crc << 1)
    return crc 
    
  def getCrc(self,data):
    return struct.unpack('<'+'I',data[-4:])[0]

  def isCrcValid(self,data):
    gotCrc=self.getCrc(data[-4:])
    if sys.version_info <= (3, 0):
      tmp =[]
      for i in data:
        tmp.append(ord(i))
      data = tmp
    calcCrc = self.calcCrc32(data,len(data)-4)
    if(calcCrc==gotCrc):
      return True
    else:
      raise Exception("CRC not valid!! Received: 0x{:08x} !=\n                         Calculated: 0x{:08x} ".format(gotCrc,calcCrc))
    
    
    