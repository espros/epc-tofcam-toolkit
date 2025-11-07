import pytest
from epc.tofCam660 import TOFcam660
import time
from ..config import DUT_CONFIG


@pytest.fixture(scope="function")
def cam():
    # Get the list of configuration values to parametrize over
    if "dut_TOFcam660" not in DUT_CONFIG:
        pytest.skip('Camera unavailable for this test.')
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam660"]
    cam: TOFcam660 = cam_class(**interface)
    init(cam)
    yield cam
    restart(cam)
    cam.__del__()

def restart(tofCam: TOFcam660):
    tofCam.device.system_reset()
    # tofCam.device.power_reset()
    time.sleep(10)

def init(tofCam: TOFcam660):
    pass


# How to run this test:
#   pytest tests/tofCam660/test_powercycle.py -m manualTest -s
#
#   Note 1: When trying to run this with the ▶ button on the left of the method
#           in vscode, you might have to remove the manualTest mark.
#   Note 2: This test power cycles the camera for 'execution_number' of times
#           Use this as a base for testing startup behaviour.

@pytest.mark.manualTest
@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize("capture_func", ["get_distance_and_amplitude"])
@pytest.mark.parametrize('integration_times', [[12, 34, 56, 78]])
def test_take_image(cam: TOFcam660, capture_func, integration_times, execution_number):
    # Image settings
    cam.settings.set_integration_hdr(integration_times)

    # Take image
    getattr(cam, capture_func)()

    # Compare UDP answer of image just taken
    meta = cam.frame
    int_dict  = cam.settings.get_integration_time()

    assert int_dict['grayscaleIntTime'] == integration_times[0]
    assert int_dict['lowIntTime'] == integration_times[1]
    assert int_dict['midIntTime'] == integration_times[2]
    assert int_dict['highIntTime'] == integration_times[3]

    assert meta.lowIntTime == integration_times[1]
    assert meta.midIntTime == integration_times[2]
    assert meta.highIntTime == integration_times[3]