
import numpy as np
import sys
import subprocess
import time
import struct

from epc.tofCam611.commandList import commandList
from epc.tofCam611.communicationType import communicationType
from epc.tofCam611.update import update
from epc.tofCam611.constants import __constants  as Constants
from epc.tofCam_lib.crc import Crc, CrcMode
from epc.tofCam_lib.transformations_3d import Lense_Projection, depth_to_3d

class Camera():
  MIN_AMP_ERROR = 16001000
  def __init__(self,com,comDll=None):
    self.comDll=comDll
    self.com = com
    self.resolution = (8, 8) #(x,y)
    self.maxDepth = 16000 # pixel code limit for valid data 
    self.crc = Crc(mode=CrcMode.CRC32_STM32, revout=False)
    self.minAmplitude = 50
    self.powerOn()
    self.setIntTime_us(50)

  def powerOn(self,enable=True):
    self.tofWrite([commandList.COMMAND_SET_POWER, enable])
    time.sleep(1)
    self.getAcknowledge()

  def getProductionDate(self):
    """
    get Production info
    @return [productionYear, productionWeek]
    """
    self.tofWrite(commandList.COMMAND_GET_PRODUCTION_INFO)
    tmp = self.getAnswer(communicationType.DATA_PRODUCTION_INFO,10)
    productionWeek= tmp[1]
    productionYear= tmp[0]
    return [productionYear,productionWeek]

  def getIntTime_us(self):
    """
    get integration Time in µSeconds
    """
    self.tofWrite(commandList.COMMAND_GET_INTEGRATION_TIME_3D)
    tmp = self.getAnswer(communicationType.DATA_INTEGRATION_TIME,10)
    return tmp[0]+tmp[1]*0x100
  
  def setMinAmplitude(self, minAmp):
    """
    set minimal amplitude for distance estimation
    """
    self.minAmplitude = minAmp

  def setIntTime_us(self, integrationTime):
    """
    set integration Time in µSeconds
    """
    if integrationTime>=Constants.MAX_INTEGRATION_TIME:
      integrationTime=Constants.MAX_INTEGRATION_TIME
    self.tofWrite([commandList.COMMAND_SET_INTEGRATION_TIME_3D, 0 , integrationTime &0xff, (integrationTime>>8)&0xff])
    self.getAcknowledge()

  def readRegister(self, address):
    """
    Get Register of epc611 via SPI

    @param address spi address of register 0-0xff

    @return 16bit spi command returned from chip
    """
    page= address//Constants.epc611.PAGE_LENGTH
    shortAddress= address-page*Constants.epc611.PAGE_LENGTH
    self.tofWrite([commandList.COMMAND_READ_REGISTER,shortAddress,page])
    tmp = self.getAnswer(communicationType.DATA_REGISTER,10)
    return tmp[0]

  def writeRegister(self, address, data):
    """
    Set Register of epc611 via SPI

    @param address spi address of register 0-0xff
    @param data new value of selected Register

    @return 16bit spi command returned from chip
    """
    page = address//Constants.epc611.PAGE_LENGTH
    shortAddress = address - page*Constants.epc611.PAGE_LENGTH
    self.tofWrite([commandList.COMMAND_WRITE_REGISTER,shortAddress,page,data])
    tmp = self.getAnswer(communicationType.DATA_REGISTER,10)

  def getRegisterDump(self):
    for register in range(256):
      print(f'{hex(register)}, {hex(self.readRegister(register))}')

  def getChipInfo(self):
    """
    read chip information
    @return [chipId, waferId]
    """
    self.tofWrite(commandList.COMMAND_GET_CHIP_INFORMATION)
    tmp = self.getAnswer(communicationType.DATA_CHIP_INFORMATION,12)
    raw=list(struct.unpack('<'+'H'*2,tmp))
    chipId= raw[0]
    waferId= raw[1]
    return [chipId, waferId]

  def getIdentification(self,getSum=False):
    """
    get identification for device
    @return identification
    """
    self.tofWrite(commandList.COMMAND_IDENTIFY)
    answer = self.getAnswer(communicationType.DATA_IDENTIFICATION,12)
    answer =struct.unpack('<'+'BBBB',answer)
    chipType = answer[2]
    device = answer[1]
    version = answer[0]
    if getSum:
      return chipType*0x10000+device*0x100+version
    else:
      return [chipType,device,version]

  def getFwRelease(self):
    """
    get firmware release
    @return firmware release [major, minor]
    """
    self.tofWrite([commandList.COMMAND_GET_FIRMWARE_RELEASE])
    answer = self.getAnswer(communicationType.DATA_FIRMWARE_RELEASE,12)
    fwRelease=struct.unpack('<'+'I',answer)[0]
    fwVersionMajor = fwRelease>>16
    fwVersionMinor = fwRelease&0xffff
    return [fwVersionMajor,fwVersionMinor]

  def setDllStep(self,step=0):
    self.tofWrite([commandList.COMMAND_SET_DLL_STEP,step])
    self.getAcknowledge()

  def setModFrequency(self,modClock):
    self.tofWrite([commandList.COMMAND_SET_MODULATION_FREQUENCY,modClock])
    self.getAcknowledge()

  def setFilter(self, temporalThreshold, temporalFactor):
    self.tofWrite([commandList.COMMAND_SET_FILTER,  temporalThreshold &0xff, (temporalThreshold>>8)&0xff, temporalFactor&0xff,  (temporalFactor>>8)&0xff])
    self.getAcknowledge()

  def getChipTemperature(self):
    self.tofWrite(commandList.COMMAND_GET_TEMPERATURE)
    tmp = self.getAnswer(communicationType.DATA_TEMPERATURE,10)
    temperature=struct.unpack('<'+'h',tmp)[0]
    return temperature/100.0

  def getFrames(self,frames=150,intTime=140):
    self.setIntTime(intTime)
    [dcsRaw,distanceRaw,amplitudeRaw]=self.getDDA()
    dcsMatrix=np.ones((dcsRaw.shape[0],frames))+np.nan #python 3 *dcsRaw
    distanceMatrix=np.ones((frames))+np.nan
    amplitudeMatrix=np.ones((frames))+np.nan
    for frameIdx in np.arange(frames):
      #Get picture data and save it
      [dcsRaw,distanceRaw,amplitudeRaw]=self.getDDA()
      dcsMatrix[:,frameIdx]= dcsRaw[:,0,0]
      distanceMatrix[frameIdx]= distanceRaw[0,0]
      amplitudeMatrix[frameIdx]= amplitudeRaw[0,0]
      self.dcsMatrix=np.copy(dcsMatrix)
      self.distanceMatrix=np.copy(distanceMatrix)
      self.amplitudeMatrix=np.copy(amplitudeMatrix)
    stdDcs=np.std(dcsMatrix,axis=-1)
    dcsMatrix=np.mean(dcsMatrix,axis=-1)
    stdDistance=np.std(distanceMatrix)
    distanceMatrix=np.mean(distanceMatrix)
    stdAmplitude=np.std(amplitudeMatrix)
    amplitudeMatrix=np.mean(amplitudeMatrix)

  def getError(self):
    self.tofWrite([commandList.COMMAND_GET_ERROR])
    [tmp,length] = self.getData(communicationType.DATA_ERROR)
    return np.array((struct.unpack('<'+'i',tmp[:4])))

  def getDcs(self):
    self.tofWrite([commandList.COMMAND_GET_DCS])
    [tmp,length] = self.getData(communicationType.DATA_DCS)
    if length == 12:
      dcsRaw=np.array((struct.unpack('<'+'i'*4,tmp)))
      dcs=dcsRaw
    elif length == 8:
      dcsRaw=np.array((struct.unpack('<'+'h'*4,tmp)))
      dcs=dcsRaw
    else:
      dcsRaw=np.array((struct.unpack('<'+'h'*int(length/2),tmp)))
      dcs = np.reshape(dcsRaw,(4,8,8))
    return dcs

  def getDistance(self):
    if(self.getDeviceType() == "TOFframe"):
      dist, amp =  self.getDistAmpl()
      dist[amp < self.minAmplitude] = self.MIN_AMP_ERROR
    elif(self.getDeviceType() == "TOFrange"):
      dist, amp =  self.getDistAmpl()
      dist = dist.reshape(-1, 1)
      amp = amp.reshape(-1, 1)
      dist[amp < self.minAmplitude] = self.MIN_AMP_ERROR
    return dist

    # self.tofWrite([commandList.COMMAND_GET_DISTANCE])
    # [tmp,length] = self.getData(communicationType.DATA_DISTANCE)
    # if length == 4:
    #   distRaw  =np.array((struct.unpack('<'+'I',tmp)))
    #   distance=distRaw
    # else:
    #   distRaw=np.array((struct.unpack('<'+'I'*int(length/4),tmp)))
    #   distance = np.reshape(distRaw,(8,8))
    # return distance/Constants.CONVERT_TO_MM

  def getDeviceType(self,device=None):
    if device == None:
      deviceIdentification = self.getIdentification()
      deviceType = deviceIdentification[1]

    if deviceType == Constants.DEVICE_TOFRANGE:
      device = "TOFrange"
    if deviceType == Constants.DEVICE_TOFFRAME:
      device = "TOFframe"

    return device


  def getAmplitude(self):
    if(self.getDeviceType() == "TOFframe"):
      self.tofWrite([commandList.COMMAND_GET_AMPLITUDE])
      [tmp,length] = self.getData(communicationType.DATA_AMPLITUDE)
      if length == 4:
        amplRaw =np.array((struct.unpack('<'+'I',tmp)))
        amplitude=amplRaw
      else:
        amplRaw=np.array((struct.unpack('<'+'I'*int(length/4),tmp)))
        amplitude = np.reshape(amplRaw,(8,8))
    elif(self.getDeviceType() == "TOFrange"):
      self.tofWrite([commandList.COMMAND_GET_AMPLITUDE])
      [tmp,length] = self.getData(communicationType.DATA_AMPLITUDE)
      amplRaw =np.array((struct.unpack('<'+'I',tmp)))
      amplitude=amplRaw.reshape(-1, 1)
    return amplitude

  def getDistAmpl(self):
    self.tofWrite([commandList.COMMAND_GET_DISTANCE_AMPLITUDE])
    [tmp,length] = self.getData(communicationType.DATA_DISTANCE_AMPLITUDE)
    if length == 8:
      distRaw =np.array((struct.unpack('<'+'I',tmp[:-4])))
      distance=distRaw
      amplRaw =np.array((struct.unpack('<'+'I',tmp[4:])))
      amplitude=amplRaw
    else:
      distRaw   = np.array((struct.unpack('<'+'I'*(length//8),tmp[:length//2])))
      distance  = np.reshape(distRaw,(8,8))
      amplRaw   = np.array((struct.unpack('<'+'I'*(length//8),tmp[length//2:])))
      amplitude = np.reshape(amplRaw,(8,8))
    return [distance/Constants.CONVERT_TO_MM,amplitude]
  
  def getPointCloud(self):
      # capture depth image & corrections
      depth = self.getDistance().reshape(-1, 1)
      depth  = depth.astype(np.float32)
      depth[depth >= self.maxDepth] = np.nan

      # calculate point cloud from the depth image
      points = 1E-3 * depth_to_3d(np.fliplr(depth), resolution=self.resolution, focalLengh=40) # focul lengh in px (0.8 mm)
      points = np.transpose(points, (1, 2, 0))
      points = points.reshape(-1, 3)
      return points   

  def getCalibrationData(self,device=None):
    if device == None:
      [chip,device,version]=self.getIdentification()
    self.tofWrite([commandList.COMMAND_GET_CALIBRATION])
    [tmp,length] = self.getData(communicationType.DATA_CALIBRATION_DATA)
    if device == Constants.DEVICE_TOFRANGE :
      calibData=np.array((struct.unpack('<'+'h'*int(length/2),tmp))).astype(np.int16)
    if device == Constants.DEVICE_TOFFRAME :
      calibData=np.array((struct.unpack('<'+'b'*length,tmp))).astype(np.int8)
    return calibData

  def writeCalibrationDataDevice(self,val,device = None):
    """
    Write calibration data to chip!
    Caution: the data will be written in the register as sended, so combine
    uint8_t or uint16_t to uint32
    """
    if device == None:
      [chip,device,version]=self.getIdentification()

    if type(val)== list:
      val=np.array((val))
    size = len(val.tobytes())
    pwd =0x654321
    self.tofWrite([commandList.COMMAND_WRITE_CALIBRATION_DATA,\
                   Constants.calibration.writeCalibrationData.START_FLAG,\
                   np.right_shift(pwd,0) &0xff,\
                   np.right_shift(pwd,8) &0xff,\
                   np.right_shift(pwd,16) &0xff,\
                   np.right_shift(size,0) &0xff,\
                   np.right_shift(size,8) &0xff,\
                   np.right_shift(size,16) &0xff,\
                   np.right_shift(size,24) &0xff])

    self.getAcknowledge()

    idx = 0
    byteIdx=0

    if device == Constants.DEVICE_TOFRANGE:
      if len(val) & 0x01:
        val=np.insert(val,0,-1,axis=0)

      for i in range(int(len(val)/2)):
        b0= bytearray(val[i*2].tobytes())
        while len(b0)<2:
          b0.append(0)
        b0=b0[:2]
        b1= bytearray(val[i*2+1].tobytes())
        while len(b1)<2:
          b1.append(0)
        b1=b1[:2]
        b=b0+b1

        byteIdx = idx*4
        self.tofWrite([commandList.COMMAND_WRITE_CALIBRATION_DATA,\
                       Constants.calibration.writeCalibrationData.WRITE_FLAG,\
                       byteIdx&0xff,(byteIdx>>8)&0xff,(byteIdx>>16)&0xff,\
                       b[0],b[1],b[2],b[3]])
        self.getAcknowledge()
        idx +=1
    else:
      val=val.astype(np.uint8)

      for i in range(int(len(val))//4):
         byteIdx = idx*4
         self.tofWrite([commandList.COMMAND_WRITE_CALIBRATION_DATA,\
                Constants.calibration.writeCalibrationData.WRITE_FLAG,\
                byteIdx&0xff,(byteIdx>>8)&0xff,(byteIdx>>16)&0xff,\
                val[byteIdx+0],val[byteIdx+1],val[byteIdx+2],val[byteIdx+3]])
         self.getAcknowledge()
         idx +=1

    self.tofWrite([commandList.COMMAND_WRITE_CALIBRATION_DATA,\
                   Constants.calibration.writeCalibrationData.COMPLETE_FLAG])
    self.getAcknowledge()
    print("Write to Flash complete!")

  # basic functions needed for commands
  def tofWrite(self,values,ext=False):
    """
    convert list of bytes to the format of the evalkit
    @param values bytes of command
    """
    if type(values)!=list:
      values = [values]
    values += [0] * (9 - len(values)) #fill up to size 9 with zeros
    a=[0xf5]*14
    a[1:10]=values

    crc = np.array(self.crc.calculate(a[:10]))
    
    a[10] = crc & 0xff
    a[11] = (crc>>8) & 0xff
    a[12] = (crc>>16) & 0xff
    a[13] = (crc>>24) & 0xff

    if ext:
      self.comDll.write(a)
    else:
      self.com.write(a)

  def getAnswer(self,typeId,length):
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
      raise Exception("Not enought bytes!!")
    if sys.version_info[0] < 3:
      if typeId != ord(tmp[1]):
        raise Exception("Wrong Type!!:%02x"%tmp[1])
    else:
      if typeId != tmp[1]:
        raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))
      if typeId == communicationType.DATA_NACK:
        raise Exception("NACK")
    length= struct.unpack('<'+'H',tmp[2:4])[0]
    return tmp[4:4+length]

  def getData(self,typeId):
    """
    reads picture data from serial command
    @param typeId expected typeId

    @returns [data, length]
    """
    tmp=self.com.read(4)
    total = bytes(tmp)
    length = struct.unpack('<'+'H',tmp[2:4])[0]
    tmp = self.com.read(length+4)
    total+=bytes(tmp)
    self.crc.verify(total[:-4], total[-4:])
    if typeId != total[1]:
      raise Exception("Wrong Type! Expected 0x{:02x}, got 0x{:02x}".format(typeId,tmp[1]))

    return [tmp[:-4],length]


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
    if tmp[1] != communicationType.DATA_ACK:
      raise Exception("Got wrong type!:{:02x}".format(tmp[1]))
      return False
    if len(tmp) != LEN_BYTES:
      raise Exception("Not enought bytes!")
      return False
    return True

  def loadFirmware(self,filename):
    """
		load firmware to device, on device ID missmatch the firmware gets rejected
    """
    deviceID=self.getIdentification(getSum=True)
    file = open(filename,'rb')
    binData = file.raw.readall()
    fileIDraw = binData[:3]

    fileId = fileIDraw[0]+fileIDraw[1]*0x100+fileIDraw[2]*0x10000
    file.close()
    if deviceID != fileId and deviceID !=0xffffff:
      raise Exception("FirmwareID not consistent!\nBinary File: {:d} != {:d}: \
                      on device".format(fileId,deviceID))


    dataSize=struct.pack('<'+'L',len(binData))
    pwList = struct.pack('<'+'L',update.PASSWORD_DELETE)[:3]
    self.tofWrite([commandList.COMMAND_JUMP_TO_BOOTLOADER])
    self.getAcknowledge()
    self.tofWrite([commandList.COMMAND_UPDATE_FIRMWARE,\
                   update.CONTROL_START]+\
                   list(pwList)+list(dataSize))
    self.getAcknowledge()
    file = open(filename,'rb')
    index = 0
    while index < len(binData):
      indexBin=struct.pack('<'+'L',index)[:3]

      self.tofWrite([commandList.COMMAND_UPDATE_FIRMWARE,\
                     update.CONTROL_WRITE_DATA]+\
                     list(indexBin)+list(binData[index:index+4]))
      self.getAcknowledge()
      index+=4
      sys.stdout.write('\r# Loading Firmware: {:3.0f}%'.format(index/len(binData)*100))
      sys.stdout.flush()

    self.tofWrite([commandList.COMMAND_UPDATE_FIRMWARE,2])
    self.getAcknowledge()
