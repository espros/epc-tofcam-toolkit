import pytest
from epc.tofCam611 import TOFcam611
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

    def test_getPointCloud(self, cam):
        pc = cam.getPointCloud()

        assert pc.shape == (8*8, 3)