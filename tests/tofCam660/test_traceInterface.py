import pytest
from epc.tofCam660.interface import TraceInterface

@pytest.mark.skip(reason="Need to mock the socket connection to the camera.")
def test_traceInterface():
    interface = TraceInterface()
    interface.startLogging("test_traceInterface.log")
    assert None != interface