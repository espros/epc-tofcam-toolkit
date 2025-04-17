import pytest
from epc.tofCam635 import TOFcam635


@pytest.mark.systemTest
class TestTofCam635:
    def test_createTofCam635():
        cam = TOFcam635(port='/dev/ttyACM0')
        chipId, waferId = cam.cmd.getChipInfo()
        assert cam is not None
        assert chipId != 0
        assert waferId != 0