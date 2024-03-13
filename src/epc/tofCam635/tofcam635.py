"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""
import numpy as np
from epc.tofCam635.communication import *
from epc.tofCam635.commands import Commands
from epc.tofCam_lib.transformations_3d import Lense_Projection

class TofCam635:
  CAPTURE_MODE = 1
  CAPTURE_TRYS_BEFORE_FAIL = 10
  def __init__(self, port = '/dev/ttyACM0'):
    self.com = SerialInterface(port)
    self.cmd = Commands(self.com,self.com)

    self.resolution = (60, 160) #(y,x)
    self.set_default_parameters()

    self.maxDepth = 16000 # pixel code limit for valid data 
    self.lensProjection = Lense_Projection.from_lense_calibration(lensType='Wide Field', width=self.resolution[1], height=self.resolution[0])
    
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

  def get_distance_image(self, mode=0, rotate=True):
    for i in range(self.CAPTURE_TRYS_BEFORE_FAIL):
      try:
        image = self.cmd.getDistance(mode)
        image = np.reshape(image, self.resolution)
        if rotate:
          image = np.rot90(image, 1)
        return image
      except:
        continue
    raise Exception("Failed to get distance image")
  
  def get_amplitude_image(self, mode=0):
    for i in range(self.CAPTURE_TRYS_BEFORE_FAIL):
      try:
        image = self.cmd.getDistanceAndAmplitude(mode)
        amplitude = image[1::2]
        amplitude = np.reshape(image[1::2], self.resolution)
        return np.rot90(amplitude, 1)
      except:
        continue
    raise Exception("Failed to get amplitude image")
  
  def get_grayscale_image(self, mode=0):
    for i in range(self.CAPTURE_TRYS_BEFORE_FAIL):
      try:
        image = self.cmd.getGrayscale(mode)
        image = np.reshape(image, self.resolution).astype(np.uint8)
        return np.rot90(image, 1)
      except:
        continue
    raise Exception("Failed to get grayscale image")
  
  def get_point_cloud(self, mode=0):
    # capture depth image & corrections
    depth = self.get_distance_image(mode, rotate=False)
    depth  = depth.astype(np.float32)
    depth[depth >= self.maxDepth] = np.nan

    # calculate point cloud from the depth image
    points = 1E-3 * self.lensProjection.transformImage(np.fliplr(depth.T))
    points = np.transpose(points, (1, 2, 0))
    points = points.reshape(-1, 3)
    return points

  def __del__(self):
    if hasattr(self, 'com'):
      self.com.close()

  def __main__(self):
    pass
  
