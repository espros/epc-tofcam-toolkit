
from epc.tofCam660 import TOFcam660
import numpy as np

def test_hw_trigger_distance_amplitude(cam:TOFcam660):
    print("new get_hw trigger distance,amplitude image")
    cam.settings.set_hw_trigger_data_type(0)
    d, a = cam.get_hw_trigger_image(0)
    assert d.shape == (240, 320), "Distance shape mismatch"
    assert a.shape == (240, 320), "Amplitude shape mismatch"
    assert np.issubdtype(d.dtype, np.number), "Distance not numeric"
    assert np.issubdtype(a.dtype, np.number), "Amplitude not numeric"

def test_hw_trigger_grayscale(cam : TOFcam660):
    print("new get_hw trigger grayscale image")
    cam.settings.set_hw_trigger_data_type(3)
    g = cam.get_hw_trigger_image(3)
    assert g.shape == (240, 320), "Grayscale shape mismatch"
    assert np.issubdtype(g.dtype, np.number), "Grayscale not numeric"

cam = TOFcam660()
chip_id, wafer_id = cam.device.get_chip_infos()
print(f"Chip_id:{chip_id}")
test_hw_trigger_distance_amplitude(cam)
#test_hw_trigger_grayscale(cam)
cam.__del__()