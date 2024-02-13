
import serial as Serial
import sys

class SerialInterface():
  def __init__(self, port,baudrate = 921600, timeout = 0.5): 
    self.serial=Serial.Serial(port,baudrate,timeout=timeout)

  def open(self,port,baudrate = 921600, timeout = 0.5):
    self.serial=Serial.Serial(port,baudrate,timeout=timeout)

  def write(self,data):
    """
    Write serial data to device
    This function checks python version and handles version 2 and 3
    """
    if(type(data)!=list):
      #if data is not a list then make as one
      data=[data]
      
    if sys.version_info[0] >= 3:
      #python 3
      self.serial.write(bytes(data))
    else:
      #python 2
      str=''
      for i in data:
        str+=chr(i)
      self.serial.write(str)
      
  def read(self,length):
    """
    Reads and returns amount of length on serial port
    """
    return self.serial.read(length)
    
  def close(self):
    self.serial.close()
    
  def clear(self):
     self.serial.readline()
     self.serial.readline()
    # """
    # Clear serial buffer
    # """
    # while True:
      # tmp = self.serial.readline()
      # if tmp = '':
        # break
      