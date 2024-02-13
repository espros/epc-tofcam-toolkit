"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

from .communication import *
from .commands import Commands


class TofCam635():
  def __init__(self,port = 'COM3'):
    self.com = SerialInterface(port)#28
    self.cmd = Commands(self.com,self.com)

    pass
  def __del__(self):
    self.com.close()

  def __main__(self):
    pass
  
  
  
  
#{if __name__ == '__main__':
#  ek = TofCam635()
  