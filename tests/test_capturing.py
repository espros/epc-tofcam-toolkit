import pytest
import numpy as np
from epc.tofCam_lib import TOFcam
from .config import DUT_FIXTURES, cam660, cam635, cam611, camrange


@pytest.fixture(scope="function")
def cam(request):
    return request.getfixturevalue(request.param)


@pytest.mark.systemTest
@pytest.mark.parametrize("cam", DUT_FIXTURES, indirect=True)
class Test_general_calls:
    def test_capturing(self, cam: TOFcam):
        gray = cam.get_grayscale_image()
        assert isinstance(gray, np.ndarray)

        dist = cam.get_distance_image()
        assert isinstance(dist, np.ndarray)

        amp = cam.get_amplitude_image()
        assert isinstance(amp, np.ndarray)
