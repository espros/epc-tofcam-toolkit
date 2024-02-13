"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

from . import __mode
from . import __modFrequency

VERSION=2.2

MAX_INTEGRATION_TIME = 2**16-1
MAX_INTEGRATION_TIME_US = 1600
MIN_INTEGRATION_TIME_US = 10

modFrequency = __modFrequency
mode = __mode
