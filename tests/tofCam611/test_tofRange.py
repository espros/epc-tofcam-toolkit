import pytest
from epc.tofCam611 import TOFcam611
from ..config import camrange as cam


@pytest.mark.systemTest
class Test_TOFrange:
    def test_getChipInfos(self, cam: TOFcam611):
        chipId, waferId = cam.device.get_chip_infos()
        assert chipId != 0
        assert waferId != 0
        assert isinstance(chipId, int)
        assert isinstance(waferId, int)

    def test_getPointCloud(self, cam: TOFcam611):
        points, amplitude = cam.get_point_cloud()
        assert points.shape == (3, 1)
        assert amplitude.shape == (1,)