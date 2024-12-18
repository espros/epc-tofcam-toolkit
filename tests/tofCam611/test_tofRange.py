import pytest
import numpy as np
from epc.tofCam611 import TOFcam611
from epc.tofCam611.serialInterface import SerialInterface

@pytest.fixture
def cam():
    cam = TOFcam611()
    cam.initialize()
    return cam

@pytest.mark.systemTest
class Test_TOFrange:
    def test_getChipInfos(self, cam):
        chipId, waferId = cam.device.get_chip_infos()

        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)

    def test_getPointCloud(self, cam):
        pc = cam.get_point_cloud()

        assert pc.shape == (1, 3)