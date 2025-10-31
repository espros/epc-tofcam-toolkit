import pytest
from epc.tofCam635 import TOFcam635
from ..config import DUT_CONFIG


@pytest.fixture(scope='module')
def cam():
    # Get the list of configuration values to parametrize over
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam635"]
    cam: TOFcam635 = cam_class(**interface)
    cam.initialize()
    return cam


@pytest.mark.systemTest
class TestTofCam635:
    def test_getChipInfos(self, cam: TOFcam635):
        chipId, waferId = cam.device.get_chip_infos()
        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)

    def test_getPointCloud(self, cam: TOFcam635):
        pc = cam.get_point_cloud()
        assert pc.shape == (160*60, 3)