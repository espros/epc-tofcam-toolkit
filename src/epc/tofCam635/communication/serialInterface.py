"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""


import serial as Serial
import serial.tools.list_ports
import sys
import logging

log = logging.getLogger('COM')

class SerialInterface():
  def __init__(self, port: None, baudrate = 10000000, timeout = 0.2):
    if port == None:
      port = self.find_ports()

    self.serial=Serial.Serial(port,baudrate,timeout=timeout)
    self.port = port
    self.baudrate = baudrate
    self.timeout = timeout

  def find_ports(self):
    result = None
    ports = serial.tools.list_ports.comports()
    if len(ports) == 0:
      raise('No serial port found')
    for port in ports:
      if port.vid == 1155:
        log.info(f'Found serial device:')
        log.info(f'port: {port.device}, desc: {port.description}, vendor id: {port.vid}')
        result = port.device
    
    if result == None:
      raise ConnectionError('Device not found')
    return result

  def open(self,port,baudrate = 10000000, timeout = 0.2):
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
     #self.serial.flushInput()
     #self.serial.flush()
     #self.serial.readline()
     #self.serial.readline()
     #self.serial.reset_input_buffer();
     #self.serial.close()
     #self.open(self.port)
     #self.serial.reset_input_buffer();
     while True:
       tmp = self.serial.read(1000000)
       if len(tmp) == 0:
         break

     while True:
       tmp = self.serial.read(1000000)
       if len(tmp) == 0:
         break

     while True:
       tmp = self.serial.read(1000000)
       if len(tmp) == 0:
         break
     #self.serial.flushInput();
     #self.serial.readline()
    # """
    # Clear serial buffer
    # """
    # while True:
      # tmp = self.serial.readline()
      # if tmp = '':
        # break
