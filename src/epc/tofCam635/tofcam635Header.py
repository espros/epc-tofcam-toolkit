"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 08:21:41 2019

@author: mwi
"""
import struct

SIZE_HEADER = 80                   # Size of the header
INDEX_TEMPERATURE = 69             # Byte index of the temperature
INDEX_SPOT_DISTANCE = 72           # Byte index of the spot distance
INDEX_WIDTH = 12                   # Byte index of the image width
INDEX_HEIGHT = 14
INDEX_MODULATION_CHANNEL = 66

class TofCam635Header():
    def __init__(self):
        self.temperature = 4711
        self.spotDistance = 0xFFFF
        self.width = 0
        self.height = 0
        self.modulationChannel = 0

    def getHeaderSize(self):
        return SIZE_HEADER

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
        self.temperature = struct.unpack('<h', data[INDEX_TEMPERATURE:INDEX_TEMPERATURE+2])[0] / 100.0  # Change from centi degree to degree
        self.spotDistance = struct.unpack('<h', data[INDEX_SPOT_DISTANCE:INDEX_SPOT_DISTANCE+2])[0]
        self.width = struct.unpack('<h', data[INDEX_WIDTH:INDEX_WIDTH+2])[0]
        self.height = struct.unpack('<h', data[INDEX_HEIGHT:INDEX_HEIGHT+2])[0]
        self.modulationChannel = struct.unpack('B', bytes([data[INDEX_MODULATION_CHANNEL]]))[0]