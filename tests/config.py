import pytest
from epc.tofCam660 import TOFcam660
from epc.tofCam635 import TOFcam635
from epc.tofCam611 import TOFcam611


# Dictionary for pytest
DUT_CONFIG = {
    "dut_TOFcam660": (TOFcam660, {'ip_address': '10.10.31.180'}),
    "dut_TOFcam635": (TOFcam635, {'port': '/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_00000000001A-if00'}),
    # "dut_TOFcam611": (TOFcam611, {'port': '/dev/serial/by-id/usb-ESPROS_USB-UART_Adapter_DN3G8MIS-if00-port0'}),
    # "dut_TOFRange": (TOFcam611, {'port': '/dev/serial/by-id/usb-ESPROS_USB-UART_Adapter_DN29BQN1-if00-port0'})
}


@pytest.fixture(scope="function")
def cam660():
    # Get the list of configuration values to parametrize over
    if "dut_TOFcam660" not in DUT_CONFIG:
        pytest.skip('Camera unavailable for this test.')
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam660"]
    cam: TOFcam660 = cam_class(**interface)
    cam.initialize()
    yield cam
    cam.__del__()

@pytest.fixture(scope='function')
def cam635():
    # Get the list of configuration values to parametrize over
    if "dut_TOFcam635" not in DUT_CONFIG:
        pytest.skip('Camera unavailable for this test.')
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam635"]
    cam: TOFcam635 = cam_class(**interface)
    cam.initialize()
    yield cam
    cam.__del__()

@pytest.fixture(scope='function')
def cam611():
    # Get the list of configuration values to parametrize over
    if "dut_TOFcam611" not in DUT_CONFIG:
        pytest.skip('Camera unavailable for this test.')
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam611"]
    cam: TOFcam611 = cam_class(**interface)
    cam.initialize()
    yield cam
    cam.__del__()

@pytest.fixture(scope='function')
def camrange():
    # Get the list of configuration values to parametrize over
    if "dut_TOFRange" not in DUT_CONFIG:
        pytest.skip('Camera unavailable for this test.')
    (cam_class, interface) = DUT_CONFIG["dut_TOFRange"]
    cam: TOFcam611 = cam_class(**interface)
    cam.initialize()
    yield cam
    cam.__del__()

DUT_FIXTURES = ['cam660', 'cam635', 'cam611', 'camrange']