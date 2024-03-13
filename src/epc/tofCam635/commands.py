"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

import numpy as np
import struct
import sys
import time
import datetime
import logging
from time import strftime
from epc.tofCam635.communication import communicationConstants as communication
from epc.tofCam635.constants import __constants  as Constants
from epc.tofCam635 import tofcam635Header
from epc.tofCam_lib.crc import Crc, CrcMode

log = logging.getLogger('TOFcam635')

class Commands():

  def __init__(self,com,comDll=None):
    self.comDll=comDll
    self.com = com
    self.crc = Crc(mode=CrcMode.CRC32_UINT8_LIB, revout=False)

    self.printWrite=False
    self.printRead=False
    self.header = tofcam635Header.TofCam635Header()

  def setROI(self,x0=0,y0=0,x1=160,y1=60, showNotification=True):
    """
    set ROI
    """
    self.tofWrite([communication.CommandList.COMMAND_SET_ROI, x0&0xff, (x0>>8)&0xff,  y0&0xff, (y0>>8)&0xff,  x1&0xff, (x1>>8)&0xff,  y1&0xff, (y1>>8)&0xff])
    self.getAcknowledge()
    if showNotification:
      log.info('x0: {:3d} y0: {:3d} x1: {:3d} y1: {:3d}'.format(x0,y0,x1,y1))

  def setHDR(self, mode='off', showNotification=True):
    hdrMode = 0
    if mode == 'off':
      hdrMode = 0
    elif mode == 'spatial':
      hdrMode = 1
    elif mode == 'temporal':
      hdrMode = 2
    else:
      raise ValueError(f"HDR Mode '{mode}' not supported")

    self.tofWrite([communication.CommandList.COMMAND_SET_HDR, hdrMode])
    self.getAcknowledge()
    if showNotification:
      log.info('HDR mode: {}'.format(mode))

  def initCommands(self,index=0, showNotification=True):
    """
    set modulation Freuency 0=10MHz, 1=20MHz
    """

    # self.tofWrite([communication.CommandList.COMMAND_IDENTIFY])
    # answer = self.getAnswer(communication.Type.DATA_IDENTIFICATION,12)
    # self.tofWrite([communication.CommandList.COMMAND_GET_FIRMWARE_RELEASE])
    # answer = self.getAnswer(communication.Type.DATA_FIRMWARE_RELEASE,12)
    # self.tofWrite(communication.CommandList.COMMAND_GET_CHIP_INFORMATION)
    # answer = self.getAnswer(communication.Type.DATA_CHIP_INFORMATION,12)
    self.tofWrite([0x57])   #getCalibration info
    self.calibrationData = self.getAnswer(communication.Type.DATA_CALIBRATION_INFO,22)


    self.tofWrite([0x05,1])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x08,0,0])   #getCalibration info
    self.getAcknowledge()
    #self.tofWrite([0x03,0])   #getCalibration info
    #self.getAcknowledge()

    self.tofWrite([0x0A])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x0C,0x50,0x01])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x0A])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x0B])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x07,0,0,0x03,0xe8])   #getCalibration info
    self.getAcknowledge()
    #self.tofWrite([0x0f,0,0,0x03,0xe8])   #getCalibration info
    #answer = self.getAnswer(0x01,8)
    self.tofWrite([0x10,0,0])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x6c,0])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x0d,0])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([communication.CommandList.COMMAND_IDENTIFY])
    answer = self.getAnswer(communication.Type.DATA_IDENTIFICATION,12)
    self.tofWrite([communication.CommandList.COMMAND_GET_FIRMWARE_RELEASE])
    answer = self.getAnswer(communication.Type.DATA_FIRMWARE_RELEASE,12)
    self.tofWrite([communication.CommandList.COMMAND_IDENTIFY])
    answer = self.getAnswer(communication.Type.DATA_IDENTIFICATION,12)
    self.tofWrite([0x0C,0x14,0x00])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x05,1])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x0E,0,0])   #getCalibration info
    self.getAcknowledge()
    #self.tofWrite([0x04,0])   #getCalibration info
    #answer = self.getAnswer(0x01,8)
    self.tofWrite([0x01,0,0])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x08,0,0])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x6c,0])   #getCalibration info
    self.getAcknowledge()
    self.tofWrite([0x07,0,0,0x03,0xe8])   #getCalibration info
    self.getAcknowledge()
    #self.tofWrite([0x0f,0,0,0x03,0xe8])   #getCalibration info
    #answer = self.getAnswer(0x01,8)

  def setIntTimeDist(self,index, uSec,showNotification=True):
    """
    set integration Time in µSeconds
    """
    if uSec>=Constants.MAX_INTEGRATION_TIME:
      uSec=Constants.MAX_INTEGRATION_TIME
    self.tofWrite([communication.CommandList.COMMAND_SET_INT_TIME_DIST, index , uSec &0xff, (uSec>>8)&0xff])
    self.getAcknowledge()
    if showNotification:
      log.info('mode {:2d} set integration Time to: {:5d}us'.format(index, uSec))
  
  def setIntTimeGray(self,index, uSec,showNotification=True):
    """
    set integration Time in µSeconds
    """
    if uSec>=Constants.MAX_INTEGRATION_TIME:
      uSec=Constants.MAX_INTEGRATION_TIME
    self.tofWrite([communication.CommandList.COMMAND_SET_INTEGRATION_TIME_GRAYSCALE, index , uSec &0xff, (uSec>>8)&0xff])
    self.getAcknowledge()
    if showNotification:
      log.info('mode {:2d} set integration Time to: {:5d}us'.format(index, uSec))

  def setModChannel(self, channel=0, showNotificatin=True):
    if 0 > channel > 15:
      raise Exception(f'Mod Channel must be between 0-15 but was {channel}')
    
    self.tofWrite([communication.CommandList.COMMAND_SET_MOD_CHANNEL, 0, channel])
    self.getAcknowledge()
    if showNotificatin:
      log.info(f'set Modulation Channel: {channel}')

  def setModFrequency(self,index=0, showNotification=True):
    """
    set modulation Freuency 0=10MHz, 1=20MHz
    """

    self.tofWrite([communication.CommandList.COMMAND_SET_MODULATION_FREQUENCY, index])
    self.getAcknowledge()
    if showNotification:
      log.info('set Modulation Frequency: {} '.format(Constants.modFrequency.F_STRINGS[index]))

  def setBinning(self,enable=False, showNotification=True):
    """
    set binnning
    """
    self.tofWrite([communication.CommandList.COMMAND_SET_BINNING, enable])
    self.getAcknowledge()
    if showNotification:
      log.info('binning: {} '.format(enable))

  def setOperationMode(self,index=0, showNotification=True):
    """
    set modulation Freuency 0=10MHz, 1=20MHz
    """

    self.tofWrite([communication.CommandList.COMMAND_SET_OPERATION_MODE, index])
    self.getAcknowledge()
    if showNotification:
      log.info('set Operation Mode: {} '.format(Constants.mode.MODE_STRING[index]))

  def getChipInfo(self):
    """
    read chip information
    @return [chipId, waferId]
    """
    self.tofWrite(communication.CommandList.COMMAND_GET_CHIP_INFORMATION)
    tmp = self.getAnswer(communication.Type.DATA_CHIP_INFORMATION,12)
    raw=list(struct.unpack('<'+'H'*2,tmp))
    chipId= raw[0]
    waferId= raw[1]
    log.info(f'chipID:\t\t%d{chipId} WaferID:\t\t%d{waferId}')
    return [chipId, waferId]

  def getCalibrationInfo(self):
    """
    read calibration data
    @return calibration data
    """
    self.tofWrite([0x57])   #getCalibration info
    return self.getAnswer(communication.Type.DATA_CALIBRATION_INFO,22)

  def getCalibrationData(self):
    """
    read calibration data
    @return calibration data
    """
    self.tofWrite([0x43])   #getCalibration info
    [calibrationData_raw, length] = self.getLargeData(communication.Type.DATA_CALIBRATION_DATA)
    calibrationData = np.frombuffer(calibrationData_raw, dtype="h")
    return calibrationData, calibrationData_raw

    #answer = self.getAnswer(communication.Type.DATA_CALIBRATION_DATA,180)

  def writeRegister(self, register_address, value):
    self.tofWrite([communication.CommandList.COMMAND_WRITE_REGISTER, register_address, value])
    self.getAcknowledge()
    return

  def readRegister(self, register_address):
    self.tofWrite([communication.CommandList.COMMAND_READ_REGISTER, register_address])
    answer = self.getAnswer(communication.Type.DATA_REGISTER,9)
    return int(answer[0])

  def systemReset(self):
    self.tofWrite([communication.CommandList.COMMAND_SYSTEM_RESET])
    self.getAcknowledge()
    return

  def getFwRelease(self):
    """
    get firmware release
    @return firmware release [major, minor]
    """
    self.tofWrite([communication.CommandList.COMMAND_GET_FIRMWARE_RELEASE])
    answer = self.getAnswer(communication.Type.DATA_FIRMWARE_RELEASE,12)
    fwRelease=struct.unpack('<'+'I',answer)[0]
    log.info('Firmware Version: {:d}.{:d}'.format(fwRelease>>16,fwRelease&0xffff))
    return float(fwRelease>>16) + float(fwRelease&0xffff)/100

  def getTemperature(self):
    """
    get temperature
    @return temperature in degree
    """
    self.tofWrite([communication.CommandList.COMMAND_GET_TEMPERATURE])
    answer = self.getAnswer(communication.Type.DATA_TEMPERATURE,10)
    centi_temperature=struct.unpack('<'+'h',answer)[0]
    temperature = centi_temperature/100
    # log.info('Temperature (°C): '+str(temperature))
    return temperature

  def getCameraIdentification(self):
    """
    get camera identification number and the mode
    @return [HW version, device type, chip type, operation mode]
    """
    self.tofWrite([communication.CommandList.COMMAND_IDENTIFY])
    answer = self.getAnswer(communication.Type.DATA_IDENTIFICATION,12)
    temp=struct.unpack('<'+'I',answer)[0]
    oPmode=((temp&0xff000000)>>24)
    chipType=((temp&0x00ff0000)>>16)
    deviceType=((temp&0x0000ff00)>>8)
    hwVersion=(temp&0x000000ff)
    log.info('HW version: {:d} device type {:d} chip type {:d} operation mode {:d}'.format(hwVersion,deviceType,chipType,oPmode))
    return [hwVersion, deviceType, chipType, oPmode]

  def setAmplitudeLimit(self, index, limit, showNotification=True):
    """
    set amplitude limit
    """
    self.tofWrite([communication.CommandList.COMMAND_SET_AMPLITUDE_LIMIT, index, limit & 0xff, (limit>>8) & 0xff])
    self.getAcknowledge()
    if showNotification:
      log.info('Amplitude Limit: {:5d} '.format(limit))

  def setMode(self,mode):
    """
    set operation mode
    WF, NF, both, ...
    """
    self.actualMode = mode
    self.tofWrite([communication.CommandList.COMMAND_SET_OPERATION_MODE,mode])
    self.getAcknowledge()
    log.info("# Mode set to:{}".format(Constants.mode.MODE_STRING[mode]))

  def setDllStep(self,step=0,showNotification=True):
    """
    set dll step for calibration
    """
    self.tofWrite([communication.CommandList.COMMAND_SET_DLL_STEP,step])
    self.getAcknowledge()
    if showNotification:
      log.info("dll step set to:{}".format(step))

  def setMedianFilter(self, enable=False, showNotification=True):
    """
    set median filter
    """
    self.tofWrite([communication.CommandList.COMMAND_SET_MEDIAN_FILTER, int(enable)])
    self.getAcknowledge()
    if showNotification:
      log.info('Median Filter: {} '.format(enable))

  def setAverageFilter(self, enable=False, showNotification=True):
    """
    set average filter
    """
    self.tofWrite([communication.CommandList.COMMAND_SET_AVERAGE_FILTER, int(enable)])
    self.getAcknowledge()
    if showNotification:
      log.info('Average Filter: {} '.format(enable))

  def setTemporalFilter(self, enable, threshold=250, weight=10):
    if enable:
      self.tofWrite([communication.CommandList.COMMAND_SET_TEMPORAL_FILTER_WFOV,threshold & 0xff, (threshold>>8) & 0xff,weight & 0xff, (weight>>8) & 0xff])
    else:
      self.tofWrite([communication.CommandList.COMMAND_SET_TEMPORAL_FILTER_WFOV,0,0,0,0])
    self.getAcknowledge()
    if enable:
      log.info('Exponential Filter set: Threshold: {:5d}, weight: {:5d}'.format(threshold,weight))
    else:
      log.info('Exponential Filter disabled')

  def setExpFilterSpot(self,threshold = 250,weight = 10):
    self.tofWrite([communication.CommandList.COMMAND_SET_FILTER_SINGLE_SPOT,threshold & 0xff, (threshold>>8) & 0xff,weight & 0xff, (weight>>8) & 0xff])
    self.getAcknowledge()
    if threshold == 0:
      log.info('Exponential Filter Spot disabled')
    else:
      log.info('Exponential Filter Spot set: Threshold: {:5d}, weight: {:5d}'.format(threshold,weight))

  def setEdgeFilter(self, enable=False, threshold=0):
    if enable:
      self.tofWrite([communication.CommandList.COMMAND_SET_EDGE_FILTER,threshold & 0xff, (threshold>>8) & 0xff])
    else:
      self.tofWrite([communication.CommandList.COMMAND_SET_EDGE_FILTER,0,0])
    self.getAcknowledge()
    if enable:
      log.info('Edge Filter set: Threshold: {:5d}'.format(threshold))
    else:
      log.info('Edge Filter disabled')

  def setInterferenceDetection(self, enabled=False, useLastValue=False, limit=500):
    self.tofWrite([communication.CommandList.COMMAND_SET_INTERFERENCE_DETECTION, enabled, useLastValue, (limit & 0xff), (limit>>8) & 0xff])
    self.getAcknowledge()
    if enabled==False:
      log.info('Interference Detection disabled')
    else:
      log.info('Interference Detection enabled, useLastValue: {}, Limit: {:5d}'.format(useLastValue, limit))

  # def setDefaultOffset(self, offsetMM=0):
  #   offsetMM_LSB=(offsetMM&0x00ff)
  #   offsetMM_MSB=((offsetMM&0x0000ff00)>>8)
  #   self.tofWrite([communication.CommandList.COMMAND_SET_OFFSET, offsetMM_LSB,offsetMM_MSB])
  #   self.getAcknowledge()
  #   log.info('offsetMM: {}'.format(offsetMM))

  def getDcs(self, mode=0):
    """
    get dcs
    @return dcs
    """
    self.tofWrite([communication.CommandList.COMMAND_GET_DCS,mode])

    [tmp,length] = self.getLargeData(communication.Type.DATA_DCS)

    dcs = np.frombuffer(tmp, dtype="h")

    dcs = np.reshape(dcs, (4, self.header.getNumPixel()))

    return dcs

  def getGrayscale(self, mode=0):
    """
    get grayscale
    @return grayscale
    """

    self.tofWrite([communication.CommandList.COMMAND_GET_GRAYSCALE, mode])

    [tmp,length] = self.getData(communication.Type.DATA_GRAYSCALE)

    grayscaleImage = np.frombuffer(tmp, dtype="b")
    return grayscaleImage

  def getDistance(self, mode=0):
    """
    get tof distance
    """
    self.tofWrite([communication.CommandList.COMMAND_GET_DISTANCE, mode])

    # In streaming mode do not get the answer. The pyhten is anyway too slow
    if (mode >= 2):
      return 0

    [tmp,length] = self.getData(communication.Type.DATA_DISTANCE)

    distanceWithConfidence = np.frombuffer(tmp, dtype="h")

    distance = []
    confidence = []

    #Mask out distance and confidence
    for i in range(len(distanceWithConfidence)):
        distance.append(distanceWithConfidence[i] & 0x3FFF)
        confidence.append((distanceWithConfidence[i] >> 14) & 0x03)

    return distance

  def getDistanceAndAmplitude(self, mode=0):
    """
    get tof distance
    """
    self.tofWrite([communication.CommandList.COMMAND_GET_DISTANCE_AMPLITUDE, mode])

    # In streaming mode do not get the answer. The pyhten is anyway too slow
    if (mode >= 2):
      return 0

    [tmp,length] = self.getData(communication.Type.DATA_DISTANCE_AMPLITUDE)

    distAmpWithConfidence = np.frombuffer(tmp, dtype="h")

    distAmp = []
    confidence = []

    #Mask out distance and confidence
    for i in range(len(distAmpWithConfidence)):
        distAmp.append(distAmpWithConfidence[i] & 0x3FFF)
        confidence.append((distAmpWithConfidence[i] >> 14) & 0x03)

    return distAmp

  def getTimeStampStr(self):
     return datetime.datetime.fromtimestamp(time.time()).strftime('%y%m%d_%H-%M-%S')


  # basic functions needed for commands
  def tofWrite(self,values):
    """
    convert list of bytes to the format of the evalkit
    @param values bytes of command
    """
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

#   to print raw output
    self.printWriteFct(a)
    self.com.write(a)


  def printWriteFct(self,data):
    if self.printWrite:
      log.info('W:',end='')
      j=0
      for i in data:
        log.info('%02x,'%i,end = '')
        j+=1
      log.info(' - len:',j)

  def printReadFct(self,data):
    if self.printRead:
      log.info('R:',end='')
      j=0
      for i in data:
        log.info('%02x,'%i,end = '')
        j+=1
      log.info(' - len:',j)

  def getAnswer(self, typeId, length):
    """
    return answer of serial command
    @param typeId expected typeId
    @param length of returned data
    @param typeId expected typeId

    @returns data of serial port with verified checksum
    """

    tmp=self.com.read(length)
    
    if not self.crc.verify(tmp[:-4], tmp[-4:]):
      raise Exception("CRC not valid!!")
    if len(tmp) != length:
      raise Exception("Not enough bytes!!, expected {:02d}, got {:02d}".format(length, len(tmp)))
    if sys.version_info[0] < 3:
      if typeId != ord(tmp[1]):
        raise Exception("Wrong Type!!:%02x"%tmp[1])
    else:
      if typeId != tmp[1]:
        raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))
      if typeId == communication.Type.DATA_NACK:
        raise Exception("NACK")
    self.printReadFct(tmp)
    length= struct.unpack('<'+'H',tmp[2:4])[0]
    return tmp[4:4+length]


  def getData(self,typeId):
    """
    reads picture data from serial command
    @param typeId expected typeId

    @returns [data, length]
    """
    tmp=self.com.read(communication.Data.SIZE_HEADER)
    total = bytes(tmp)
    length = struct.unpack('<'+'H',tmp[communication.Data.INDEX_LENGTH:communication.Data.INDEX_LENGTH + communication.Data.SIZE_LENGTH])[0]
    tmp = self.com.read(length+4)
    total+=bytes(tmp)
    if not self.crc.verify(total[:-4], total[-4:]):
      raise Exception("CRC not valid!!")
    if typeId != total[1]:
      raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))

    self.printReadFct(total)
    self.header.extractData(tmp)

    # Remove header at beginning and checksum at the end
    return [tmp[self.header.getHeaderSize():-4],length]

  def getLargeData(self,typeId):
    """
    reads large data from serial command. Large data is sent with multiple packets
    @param typeId expected typeId

    @returns [data, length]
    """
    totalSizeDone = 0
    data = []

    #Stay here until all data is received
    while True:
        #Read enough to get the size
        tmp=self.com.read(communication.Data.SIZE_HEADER)
        total = bytes(tmp)
        length = struct.unpack('<'+'H',tmp[communication.Data.INDEX_LENGTH:communication.Data.INDEX_LENGTH + communication.Data.SIZE_LENGTH])[0]

        #Now read the whole packet
        tmp = self.com.read(length+4)

        #The packet contains the total size (sum of all packets)
        totalSize = struct.unpack('<'+'L',tmp[1:5])[0]

        #Check the CRC as usual
        total+=bytes(tmp)
        if self.crc.verify(total[:-4], total[-4:]):
          raise Exception("CRC not valid!!")
        if typeId != total[1]:
            raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))

        #Append the data
        data.extend(tmp[5:-4])
        totalSizeDone += (length - 1)

        #When the total expected size is reached, stop the loop
        if (totalSizeDone >= totalSize):
            break


    self.printReadFct(total)
    self.header.extractData(data)

    # Remove header at beginning. The checksum is already removed
    return [bytes(data[self.header.getHeaderSize():]), totalSize]


  def getAcknowledge(self,ext=False):
    """
    ask for acknowledge
    @return True if acknowledge was received otherwise return False
    """
    LEN_BYTES = 8
    if ext:
      tmp=self.comDll.read(LEN_BYTES)
    else:
      tmp=self.com.read(LEN_BYTES)
    if not self.crc.verify(tmp[:-4], tmp[-4:]):
      raise Exception("CRC not valid!!")
      return False
    if tmp[1] != communication.Type.DATA_ACK:
      raise Exception("Got wrong type!:{:02x}".format(tmp[1]))
      return False
    if len(tmp) != LEN_BYTES:
      raise Exception("Not enought bytes!")
      return False
    self.printReadFct(tmp)
    return True


  def getFileString(self):
    '''
    for same filename ovar all measurements
    '''
    """Get the file name
    Assembles a file name containing:
        - data
        - chip information
        - Type of data

    """
    chipInfo = self.getChipInfo()
    chipId = chipInfo[0]
    waferId = chipInfo[1]

    timestamp = strftime("%Y%m%d_%H%M%S")

    fileName = timestamp + "_" + str(waferId) + "_" + str(chipId);

    return fileName

  def getHeader(self):
    return self.header
