import pytest
import numpy as np
from epc.tofCam611.tofCam611 import TOFcam611
from epc.tofCam611.serialInterface import SerialInterface

@pytest.fixture
def cam():
    cam = TOFcam611()
    return cam

def test_getChipInfos(cam):
    chipId, waferId = cam.device.get_chip_infos()

    assert chipId != 0
    assert waferId != 0
    assert isinstance(chipId, int)
    assert isinstance(waferId, int)


def test_getDistance(cam):
    distance = cam.get_distance_image()
    
    assert distance.shape == (1,1)

def test_getAmplitude(cam):
    amplitude = cam.getAmplitude()

    assert amplitude.shape == (1,1)

def test_getPointCloud(cam):
    pc = cam.getPointCloud()

    assert pc.shape == (1, 3)