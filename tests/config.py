from epc.tofCam660 import TOFcam660
from epc.tofCam635 import TOFcam635
from epc.tofCam611 import TOFcam611

# Dictionary for pytest
DUT_CONFIG = {
    "dut_TOFcam660": (TOFcam660, {'ip_address': '10.10.31.180'}),
    "dut_TOFcam635": (TOFcam635, {'port': '/dev/serial/by-id/usb-STMicroelectronics_STM32_Virtual_ComPort_00000000001A-if00'}),
    "dut_TOFcam611": (TOFcam611, {'port': '/dev/serial/by-id/usb-ESPROS_USB-UART_Adapter_DN3G8MIS-if00-port0'}),
    "dut_TOFRange": (TOFcam611, {'port': '/dev/serial/by-id/usb-ESPROS_USB-UART_Adapter_DN29BQN1-if00-port0'})
}