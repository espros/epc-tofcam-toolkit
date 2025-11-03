import pytest
import numpy as np
from epc.tofCam_lib import TOFcam
from .config import DUT_CONFIG


# Get the list of configuration values to parametrize over
CAMERA_NAMES = list(DUT_CONFIG.keys()) 


@pytest.fixture(scope="module")
def cam(request):
    cam_class, interface = DUT_CONFIG[request.param]
    cam: TOFcam = cam_class(**interface)
    cam.initialize()
    return cam


@pytest.mark.systemTest
@pytest.mark.parametrize("cam", CAMERA_NAMES, indirect=True)
class Test_general_calls:
    def test_capturing(self, cam: TOFcam):
        gray = cam.get_grayscale_image()
        assert isinstance(gray, np.ndarray)

        dist = cam.get_distance_image()
        assert isinstance(dist, np.ndarray)

        amp = cam.get_amplitude_image()
        assert isinstance(amp, np.ndarray)
