
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'src', 'epc'))

import numpy as np
import pytest
from scripts.TestPWRcycleLoop import TofCam660HDRDevice
import time
import subprocess
class TofCamWrapper:
    def __init__(self, ip_address: str):    
        self.cam = TofCam660HDRDevice(ip_address)
        self.run_through = False

    def __del__(self):
        if hasattr(self, "cam") and self.cam is not None:
            self.cam.__del__()

def closing():
    print("\nWe have an issue. Stop immediately without restarting.")
    subprocess.Popen(['aplay', 'tests/fail.wav'])
    pytest.exit()

@pytest.fixture(scope="function")
def dut():
    try:
        dut = TofCamWrapper(ip_address='10.10.31.180')
        init(dut)
        check_image(dut, 16)
        yield dut
        if not dut.run_through:
            closing()
        restart(dut)
    except:
        closing()
    finally:
        if dut is not None:
            dut.__del__()

def restart(dut: TofCamWrapper):
    dut.cam.tofcam660.device.system_reset()
    # cam.tofcam660.device.power_reset()
    time.sleep(10)

def init(dut: TofCamWrapper):
    dut.cam.tofcam660.settings.set_modulation(frequency_mhz = 3)
    dut.cam.tofcam660.settings.set_illuminator_segments(segment_2_to_4 = True)

def check_image(dut: TofCamWrapper, integration_time):
    meta = dut.cam.tofcam660.frame
    int_dict  = dut.cam.tofcam660.settings.get_integration_time()
    # print(f"Integration times from UDP   : {meta.lowIntTime}, {meta.midIntTime}, {meta.highIntTime}")
    # print(f"Integration times from getter: {int_dict['lowIntTime']}, {int_dict['midIntTime']}, {int_dict['highIntTime']}, {int_dict['grayscaleIntTime']}")

    # Compare UDP answer of HDR image taken during init (default integration times)
    assert int_dict['grayscaleIntTime'] == 25
    assert int_dict['lowIntTime'] == integration_time
    assert int_dict['midIntTime'] == 0
    assert int_dict['highIntTime'] == 0
    assert meta.lowIntTime == integration_time
    assert meta.midIntTime == 0
    assert meta.highIntTime == 0

    # Check for many zeros in the image, which would mean that we have the "Corrupt data" issue
    if (meta.distance is not None):
        assert np.count_nonzero(meta.distance) >= meta.rows * meta.cols / 2
    if (meta.amplitude is not None):
        assert np.count_nonzero(meta.amplitude) >= meta.rows * meta.cols / 2

@pytest.mark.parametrize('execution_number', range(500))
@pytest.mark.parametrize("capture_func", [
                            "get_distance_and_amplitude"])
def test_take_image(dut: TofCamWrapper, capture_func, execution_number):
    integration_time = 200

    # Image settings
    dut.cam.tofcam660.settings.set_integration_time(int_time_us = integration_time)
    dut.cam.tofcam660.settings.set_minimal_amplitude(minimum = 100)

    # Take image
    getattr(dut.cam.tofcam660, capture_func)()

    # Let it check the image details
    check_image(dut, integration_time)

    dut.run_through = True