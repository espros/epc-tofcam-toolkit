import pytest
from epc.tofCam660 import TOFcam660
from ..config import cam660 as cam


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