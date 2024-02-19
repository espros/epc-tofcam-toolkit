"""
* Copyright (C) 2019 Espros Photonics Corporation
*
* Open Source Software used:
* - numpy: Copyright © 2005-2019, NumPy Developers.
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 08:21:41 2019

Utility class

@author: mwi
"""
import numpy as np

def getInt16(data, index):
    value = (data[index+1] << 8) + data[index]
    value = np.int16(value)
    return value

def getUint8(data, index):
    value = data[index]
    value = np.uint8(value)
    return value
