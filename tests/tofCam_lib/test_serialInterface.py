import pytest
from unittest.mock import Mock, MagicMock
from epc.tofCam_lib.serial_interface import SerialInterface
from epc.tofCam_lib.crc import Crc, CrcMode

class SerialMock:
    def __init__(self):
        self.write = Mock()
        self.retBuffer = bytearray([])

    def read(self, n: int):
        res = self.retBuffer[:n]
        self.retBuffer = self.retBuffer[n:]
        return res

@pytest.mark.skip(reason="no way of currently testing this")
def test_serialSend():
    crc = Crc(mode=CrcMode.CRC32_UINT8)
    serial = SerialInterface(crc, 1155, 10000000, None, 0.2)
    serial.serial = SerialMock()
    serial.retBuffer = bytearray([0xf5, 0x00, 0x00, 0x00, 0xBC, 0x7D, 0x6A, 0x77])
    respType, data = serial.transmit(0x0E, bytearray([0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
    serial.disconnect()