import pytest
from epc.tofCam660 import TOFcam660
import time

@pytest.fixture(scope="function")
def tofCam():
    tofcam = TOFcam660(ip_address='10.10.31.180')
    init(tofcam)
    yield tofcam
    restart(tofcam)
    tofcam.__del__()

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
def test_take_image(tofCam: TOFcam660, capture_func, integration_times, execution_number):
    # Image settings
    tofCam.settings.set_integration_hdr(integration_times)

    # Take image
    getattr(tofCam, capture_func)()

    # Compare UDP answer of image just taken
    meta = tofCam.frame
    int_dict  = tofCam.settings.get_integration_time()

    assert int_dict['grayscaleIntTime'] == integration_times[0]
    assert int_dict['lowIntTime'] == integration_times[1]
    assert int_dict['midIntTime'] == integration_times[2]
    assert int_dict['highIntTime'] == integration_times[3]

    assert meta.lowIntTime == integration_times[1]
    assert meta.midIntTime == integration_times[2]
    assert meta.highIntTime == integration_times[3]