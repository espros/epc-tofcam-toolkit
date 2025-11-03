import pytest
from epc.tofCam660 import TOFcam660
from ..config import DUT_CONFIG


@pytest.fixture(scope='module')
def cam():
    # Get the list of configuration values to parametrize over
    if "dut_TOFcam660" not in DUT_CONFIG:
        pytest.skip('Camera unavailable for this test.')
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam660"]
    cam: TOFcam660 = cam_class(**interface)
    cam.initialize()
    return cam


@pytest.mark.systemTest
class TestTofCam660:
    def test_getChipInfos(self, cam: TOFcam660):
        chipId, waferId = cam.device.get_chip_infos()
        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)

    def test_getPointCloud(self, cam: TOFcam660):
        points, amplitude = cam.get_point_cloud()
        assert points.shape == (3, 320 * 240)
        assert amplitude.shape == (320 * 240,)