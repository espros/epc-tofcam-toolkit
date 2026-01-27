
from epc.tofCam660 import TOFcam660
import numpy as np
import pytest

from epc.tofCam660.interface import DataType
from ..config import cam660 as cam

@pytest.mark.manualTest
def test_hw_trigger_distance_amplitude(cam:TOFcam660):
    print("new get_hw trigger distance,amplitude image")
    cam.settings.set_hw_trigger_data_type(DataType.DISTANCE_AMPLITUDE)
    d, a = cam.get_hw_trigger_image()
    assert d.shape == (240, 320), "Distance shape mismatch"
    assert a.shape == (240, 320), "Amplitude shape mismatch"
    assert np.issubdtype(d.dtype, np.number), "Distance not numeric"
    assert np.issubdtype(a.dtype, np.number), "Amplitude not numeric"

@pytest.mark.manualTest
def test_hw_trigger_grayscale(cam : TOFcam660):
    print("new get_hw trigger grayscale image")
    cam.settings.set_hw_trigger_data_type(DataType.GRAYSCALE)
    g = cam.get_hw_trigger_image()
    assert g.shape == (240, 320), "Grayscale shape mismatch"
    assert np.issubdtype(g.dtype, np.number), "Grayscale not numeric"