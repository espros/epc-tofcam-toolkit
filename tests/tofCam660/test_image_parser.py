import pytest
import random
from epc.tofCam660 import TOFcam660

@pytest.fixture(scope="module")
def cam():
    cam = TOFcam660()
    yield cam
    cam.__del__()

@pytest.fixture(scope="function", autouse=True)
def reset_settings(cam):
    """Reset camera settings before each test."""
    cam.initialize()
    cam.settings.set_hdr(False)
    cam.settings.set_integration_time(0)

@pytest.mark.parametrize("capture_func", [
    "get_distance_image",
    "get_raw_dcs_images",
    "get_amplitude_image"])
def test_metadata_no_hdr(cam, capture_func):
    int_time = random.randint(0, 4000)
    cam.settings.set_integration_time(int_time)
    getattr(cam, capture_func)()
    meta = cam.frame

    assert meta.lowIntTime == int_time
    assert meta.midIntTime == 0
    assert meta.highIntTime == 0

@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize("capture_func", [
                            "get_distance_image",
                            "get_amplitude_image"])
def test_metadata_hdr(cam, capture_func, execution_number):
    int_time_grey = random.randint(0, 4000)
    int_time_low = random.randint(0, 4000)
    int_time_mid = random.randint(0, 4000)
    int_time_high = random.randint(0, 4000)
    cam.settings.set_hdr(True)
    cam.settings.set_integration_hdr([int_time_grey, int_time_low, int_time_mid, int_time_high])
    getattr(cam, capture_func)()
    meta = cam.frame

    assert meta.lowIntTime == int_time_low
    assert meta.midIntTime == int_time_mid
    assert meta.highIntTime == int_time_high
