from epc.tofCam660 import TOFcam660
from epc.tofCam635 import TOFcam635
from epc.tofCam611 import TOFcam611
from epc.tofCam_lib import TOFcam
import numpy as np
import pytest

@pytest.mark.parametrize("cam_class, port", [
    (TOFcam660, {}),
    (TOFcam635, {'port': '/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_00000000001A-if00'}),
    (TOFcam611, {'port': '/dev/serial/by-id/usb-ESPROS_USB-UART_Adapter_DN3G8MIS-if00-port0'}), #TOFcam
    # (TOFcam611, {'port': '/dev/serial/by-id/usb-ESPROS_USB-UART_Adapter_DN29BQN1-if00-port0'}) #TOFRange
])
def test_capturing(cam_class, port):
    cam: TOFcam = cam_class(**port)
    cam.initialize()

    gray = cam.get_grayscale_image()
    assert isinstance(gray, np.ndarray)

    dist = cam.get_distance_image()
    assert isinstance(dist, np.ndarray)

    amp = cam.get_amplitude_image()
    assert isinstance(amp, np.ndarray)
