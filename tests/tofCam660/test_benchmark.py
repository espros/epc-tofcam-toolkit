import pytest
from epc.tofCam660 import TOFcam660
import time
from typing import Literal
import datetime
import os
import matplotlib.pyplot as plt
from ..config import cam660 as cam


# How to run this test:
#   pytest tests/tofCam660/test_benchmark.py -m manualTest -s
#
#   Note 1: When trying to run this with the ▶ button on the left of the method
#           in vscode, you might have to remove the manualTest mark.
#   Note 2: This test will only print the framerate and create a history for
#           the FPS measured, but is not doing any checks at all.

@pytest.mark.manualTest
@pytest.mark.parametrize('capture_func', ['get_distance_and_amplitude'])
@pytest.mark.parametrize('integration_times', [[100, 10, 1900, 46667]])
@pytest.mark.parametrize('number_of_captures', [100])
@pytest.mark.parametrize('protocol', ['TCP', 'UDP',])
def test_fps(cam: TOFcam660,
             protocol: Literal["UDP", "TCP"],
             capture_func: str,
             integration_times: list[int],
             number_of_captures: int):
    
    # setup camera
    cam.settings.set_integration_hdr(integration_times)
    cam.device.set_data_transfer_protocol(protocol)
    cam.settings.set_hdr(False)
    cam.settings.captureMode = 0

    # clock capturing of the image(s)
    capturing_rate = []
    for _ in range(number_of_captures):
        t0 = time.perf_counter()
        getattr(cam, capture_func)()
        t1 = time.perf_counter()
        capturing_rate.append(1/(t1 - t0))

    # precautionally set protocol to default again
    cam.device.set_data_transfer_protocol("UDP")

    # editing
    fps = sum(capturing_rate) / len(capturing_rate)
    print()
    print( "┌────────────────────────────┐")
    print( "│ Measurent setup:           │")
    print(f"│   FW version :  {cam.device.get_fw_version()}       │")
    print(f"│   Protocol   :  {protocol}        │")
    print(f"│   Sample size : {f'{number_of_captures} frames':<{11}}│")
    print( "├────────────────────────────┤")
    print( "│ Measurent result:          │")
    print(f"│   Framerate   : {f'{fps:.2f} fps':<{11}}│")
    print( "└────────────────────────────┘")
    print()

    # create graph
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("logs", exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(capturing_rate, label='FPS per frame')
    plt.xlabel('Frame Number')
    plt.ylabel('FPS')
    plt.title(f'FPS over {number_of_captures} frames, protocol: {protocol}, FW: {cam.device.get_fw_version()}')
    plt.legend()
    plt.grid()
    plt.savefig(f"logs/FPS_plot_{protocol}_{timestamp}.png")
