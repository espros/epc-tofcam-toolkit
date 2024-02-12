import pytest
from epc.tofCam660.trace_interface import TraceInterface

@pytest.mark.skip(reason="Need to mock the socket connection to the camera.")
def test_traceInterface():
    interface = TraceInterface()
    assert None != interface