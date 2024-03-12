import pytest
import numpy as np
from epc.tofCam611.camera import Camera as TOFcam611
from epc.tofCam611.serialInterface import SerialInterface

@pytest.fixture
def cam():
    cam = TOFcam611(SerialInterface() )
    cam.powerOn()
    return cam

def test_getChipInfos(cam):
    chipId, waferId = cam.getChipInfo()

    assert chipId != 0
    assert waferId != 0
    assert isinstance(chipId, int)
    assert isinstance(waferId, int)


def test_getDevice(cam):
    deviceType = cam.getDeviceType()

    assert deviceType == "TOFrange"


def test_getDistance(cam):
    distance = cam.getDistance()
    
    assert distance.shape == (1,1)

def test_getAmplitude(cam):
    amplitude = cam.getAmplitude()

    assert amplitude.shape == (1,1)

def test_getPointCloud(cam):
    pc = cam.getPointCloud()

    assert pc.shape == (1, 3)