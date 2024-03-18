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

    def test_getAmplitudeImage():
        cam = TOFcam635(port='/dev/ttyACM0')
        frame = cam.get_amplitude_image()
        assert frame is not None
        assert frame.shape == (60, 160)

    def test_getGrayScaleImage():
        cam = TOFcam635(port='/dev/ttyACM0')
        frame = cam.get_grayscale_image()
        assert frame is not None
        assert frame.shape == (60, 160)