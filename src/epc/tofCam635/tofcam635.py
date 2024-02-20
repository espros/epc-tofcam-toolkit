"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""
import numpy as np
from epc.tofCam635.communication import *
from epc.tofCam635.commands import Commands


class TofCam635:
  CAPTURE_MODE = 1
  CAPTURE_TRYS_BEFORE_FAIL = 10
  def __init__(self,port = '/dev/ttyACM0'):
    self.com = SerialInterface(port)
    self.cmd = Commands(self.com,self.com)

    self.resolution = (60, 160)
    self.set_default_parameters()

  def set_default_parameters(self):
    self.set_roi(0, 0, self.resolution[1], self.resolution[0])
    self.cmd.setIntTimeGray(0, 1000)
    self.cmd.setIntTimeDist(0, 125)
    self.cmd.setIntTimeDist(1, 0)
    self.cmd.setIntTimeDist(2, 0)
    self.cmd.setIntTimeDist(3, 0)
    self.cmd.setIntTimeDist(4, 0)
    self.cmd.setModChannel(0)
    self.cmd.setHDR('off')
    self.cmd.setOperationMode(0)
    self.cmd.setMedianFilter(False)
    self.cmd.setAverageFilter(False)
    self.cmd.setEdgeFilter(False, 0)
    self.cmd.setTemporalFilter(False, 0, 0)


  def set_roi(self, x1: int, y1: int, x2: int, y2: int):
    self.resolution = (y2-y1, x2-x1)
    self.cmd.setROI(x1, y1, x2, y2)

  def set_image_type(self, image_type: str):
    if image_type == 'Distance':
      self.__capture_cb = self.get_distance_image
    elif image_type == 'Amplitude':
      self.__capture_cb = self.get_amplitude_image
    elif image_type == 'Grayscale':
      self.__capture_cb = self.get_grayscale_image
    else:
      raise ValueError(f"Image type '{image_type}' not supported")

  def get_distance_image(self, mode=0):
    for i in range(self.CAPTURE_TRYS_BEFORE_FAIL):
      try:
        image = self.cmd.getDistance(mode)
        return np.reshape(image, self.resolution)
      except:
        continue
    # raise Exception("Failed to get distance image")
  
  def get_amplitude_image(self, mode=0):
    for i in range(self.CAPTURE_TRYS_BEFORE_FAIL):
      try:
        image = self.cmd.getDistanceAndAmplitude(mode)
        amplitude = image[1::2]
        amplitude = np.reshape(image[1::2], self.resolution)
        return amplitude
      except:
        continue
    raise Exception("Failed to get amplitude image")
  
  def get_grayscale_image(self, mode=0):
    for i in range(self.CAPTURE_TRYS_BEFORE_FAIL):
      try:
        image = self.cmd.getGrayscale(mode)
        return np.reshape(image, self.resolution).astype(np.uint8)
      except:
        continue
    raise Exception("Failed to get grayscale image")

  def __del__(self):
    self.com.close()

  def __main__(self):
    pass
  
