import numpy as np
import pytest
from epc.tofCam_lib import TOFcam
from .config import DUT_CONFIG

# Get the list of configuration values to parametrize over
dut_params = list(DUT_CONFIG.values())

@pytest.mark.parametrize("cam_class, interface", dut_params)
def test_capturing(cam_class, interface):
    cam: TOFcam = cam_class(**interface)
    cam.initialize()

    gray = cam.get_grayscale_image()
    assert isinstance(gray, np.ndarray)

    dist = cam.get_distance_image()
    assert isinstance(dist, np.ndarray)

    amp = cam.get_amplitude_image()
    assert isinstance(amp, np.ndarray)
