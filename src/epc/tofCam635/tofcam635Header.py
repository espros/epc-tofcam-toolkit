"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 08:21:41 2019

@author: mwi
"""
from epc.tofCam635.communication.communicationConstants import tofcam635HeaderConstants as header
from epc.tofCam635 import util


class TofCam635Header():
    def __init__(self):
        self.temperature = 4711
        self.spotDistance = 0xFFFF
        self.width = 0
        self.height = 0
        self.modulationChannel = 0

    def getHeaderSize(self):
        return header.TofCam635HeaderConstants.SIZE_HEADER

    def getTemperature(self):
        return self.temperature
    
    def getSpotDistance(self):
        return self.spotDistance
    
    def getNumPixel(self):
        return self.width * self.height
    
    def getWidth(self):
        return self.width
    
    def getHeight(self):
        return self.height
    
    def getModulationChannel(self):
        return self.modulationChannel

    def extractData(self, data):
        self.temperature = util.getInt16(data, header.TofCam635HeaderConstants.INDEX_TEMPERATURE) / 100.0  # Change from centi degree to degree
        self.spotDistance = util.getInt16(data, header.TofCam635HeaderConstants.INDEX_SPOT_DISTANCE)
        self.width = util.getInt16(data, header.TofCam635HeaderConstants.INDEX_WIDTH)
        self.height = util.getInt16(data, header.TofCam635HeaderConstants.INDEX_HEIGHT)
        self.modulationChannel = util.getUint8(data, header.TofCam635HeaderConstants.INDEX_MODULATION_CHANNEL)