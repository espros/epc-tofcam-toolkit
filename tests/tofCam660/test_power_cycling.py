
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'src', 'epc'))

import pytest
from scripts.TestPWRcycleLoop import TofCam660HDRDevice
import time

@pytest.fixture(scope="function")
def cam():
    cam = TofCam660HDRDevice(ip_address='10.10.31.180')
    init(cam)
    check_first_image(cam)
    yield cam
    restart(cam)
    cam.__del__()

def restart(cam: TofCam660HDRDevice):
    cam.tofcam660.device.system_reset()
    # cam.tofcam660.device.power_reset()
    time.sleep(10)

def init(cam: TofCam660HDRDevice):
    cam.tofcam660.settings.set_modulation(frequency_mhz = 3)
    cam.tofcam660.settings.set_illuminator_segments(segment_2_to_4 = True)

def check_first_image(cam: TofCam660HDRDevice):
    meta = cam.tofcam660.frame
    int_dict  = cam.tofcam660.settings.get_integration_time()
    # print(f"Integration times from UDP   : {meta.lowIntTime}, {meta.midIntTime}, {meta.highIntTime}")
    # print(f"Integration times from getter: {int_dict['lowIntTime']}, {int_dict['midIntTime']}, {int_dict['highIntTime']}, {int_dict['grayscaleIntTime']}")

    # Compare UDP answer of HDR image taken during init (default integration times)
    assert int_dict['grayscaleIntTime'] == 25
    assert int_dict['lowIntTime'] == 16
    assert int_dict['midIntTime'] == 0
    assert int_dict['highIntTime'] == 0
    assert meta.lowIntTime == 16
    assert meta.midIntTime == 0
    assert meta.highIntTime == 0
    


@pytest.mark.parametrize('execution_number', range(3))
@pytest.mark.parametrize("capture_func", [
                            "get_distance_and_amplitude"])
def test_take_image(cam: TofCam660HDRDevice, capture_func, execution_number):
    integration_time = 4000

    # Image settings
    cam.tofcam660.settings.set_integration_time(int_time_us = integration_time)
    cam.tofcam660.settings.set_minimal_amplitude(minimum = 100)

    # Take image
    getattr(cam.tofcam660, capture_func)()

    # Compare UDP answer of image just taken
    meta = cam.tofcam660.frame
    int_dict  = cam.tofcam660.settings.get_integration_time()
    # print(f"Integration times from UDP   : {meta.lowIntTime}, {meta.midIntTime}, {meta.highIntTime}")
    # print(f"Integration times from getter: {int_dict['lowIntTime']}, {int_dict['midIntTime']}, {int_dict['highIntTime']}, {int_dict['grayscaleIntTime']}")

    assert int_dict['grayscaleIntTime'] == 25
    assert int_dict['lowIntTime'] == 4000
    assert int_dict['midIntTime'] == 0
    assert int_dict['highIntTime'] == 0

    assert meta.lowIntTime == integration_time
    assert meta.midIntTime == 0
    assert meta.highIntTime == 0
