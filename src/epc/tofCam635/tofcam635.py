"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""
import numpy as np
from epc.tofCam_lib import TOFcam
from epc.tofCam635.communication import *
from epc.tofCam635.commands import Commands

class TofCam635(TOFcam):
  CAPTURE_MODE = 1
  def __init__(self,port = '/dev/ttyACM0'):
    self.com = SerialInterface(port)
    self.cmd = Commands(self.com,self.com)

    self.resolution = (60, 160)
    self.set_default_parameters()

  def set_default_parameters(self):
    self.set_roi(0, 0, self.resolution[1], self.resolution[0])

  def set_roi(self, x: int, y: int, width: int, height: int):
    self.resolution = (height, width)
    self.cmd.setROI(x, y, x+width, y+height)

  def get_distance_image(self):
    for i in range(5):
      try:
        image = self.cmd.getDistance(mode=self.CAPTURE_MODE)
        return np.reshape(image,self.resolution)
      except:
        continue
    # raise Exception("Failed to get distance image")
  
  def get_amplitude_image(self):
    for i in range(5):
      try:
        image = self.cmd.getAmplitude(mode=self.CAPTURE_MODE)
        image = self.cmd.getDistanceAndAmplitude(mode=self.CAPTURE_MODE)
        amplitude = np.reshape(image[1::2], self.resolution)
        return amplitude
      except:
        continue
    raise Exception("Failed to get amplitude image")
  
  def get_grayscale_image(self):
    for i in range(5):
      try:
        image = self.cmd.getGrayscale(mode=self.CAPTURE_MODE)
        return np.reshape(image, self.resolution).astype(np.uint8)
      except:
        continue
    raise Exception("Failed to get grayscale image")

  def __del__(self):
    self.com.close()

  def __main__(self):
    pass
  