import pytest
from epc.tofCam611 import TOFcam611
from ..config import DUT_CONFIG


@pytest.fixture(scope='module')
def cam():
    # Get the list of configuration values to parametrize over
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam611"]
    cam: TOFcam611 = cam_class(**interface)
    cam.initialize()
    return cam


@pytest.mark.systemTest
class Test_TOFcam611:
    def test_getChipInfos(self, cam: TOFcam611):
        chipId, waferId = cam.device.get_chip_infos()
        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)
    
    def test_getPointCloud(self, cam: TOFcam611):
        pc = cam.get_point_cloud()
        assert pc.shape == (8*8, 3)