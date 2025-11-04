import pytest
from epc.tofCam635 import TOFcam635
from ..config import cam635 as cam


@pytest.mark.systemTest
class TestTofCam635:
    def test_getChipInfos(self, cam: TOFcam635):
        chipId, waferId = cam.device.get_chip_infos()
        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)

    def test_getPointCloud(self, cam: TOFcam635):
        points, amplitude = cam.get_point_cloud()
        assert points.shape == (3, 160 * 60)
        assert amplitude.shape == (160 * 60,)
