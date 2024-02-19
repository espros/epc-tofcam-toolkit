"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

from epc.tofCam635.communication import *
from epc.tofCam635.commands import Commands

class TofCam635():
  def __init__(self,port = 'COM3'):
    self.com = SerialInterface(port)
    self.cmd = Commands(self.com,self.com)

  def __del__(self):
    self.com.close()

  def __main__(self):
    pass
  