import pytest
from epc.tofCam635 import TofCam635

@pytest.mark.systemTest
def test_createTofCam635():
    cam = TofCam635(port='/dev/ttyACM0')
    chipId, waferId = cam.cmd.getChipInfo()
    assert cam is not None
    assert chipId != 0
    assert waferId != 0

@pytest.mark.systemTest
def test_getFrame():
    cam = TofCam635(port='/dev/ttyACM0')
    frame = cam.cmd.getDistance()
    assert frame is not None
    assert len(frame) == 160*60