import pytest
from epc.tofCam611.camera import Camera as TOFcam611
from epc.tofCam611.serialInterface import SerialInterface

@pytest.fixture
def cam():
    cam = TOFcam611(SerialInterface() )
    cam.powerOn()
    return cam

@pytest.mark.systemTest
class Test_TOFcam611:
    def test_getChipInfos(self, cam):
        chipId, waferId = cam.getChipInfo()

        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)
        

    def test_getDevice(self, cam):
        deviceType = cam.getDeviceType()

        assert deviceType == "TOFframe"


    def test_getDistance(self, cam):
        distance = cam.getDistance()

        assert distance.shape == (8,8)


    def test_getAmplitude(self, cam):
        amplitude = cam.getAmplitude()

        assert amplitude.shape == (8,8)


    def test_getPointCloud(self, cam):
        pc = cam.getPointCloud()

        assert pc.shape == (8*8, 3)