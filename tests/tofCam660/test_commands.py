from epc.tofCam660 import TOFcam660

def test_getAddress():
    cam = TOFcam660()
    cam.settings.set_flex_mod_freq(12)
    # chip_id, wafer_id = cam.device.get_chip_infos()
    # assert chip_id != 0
    # assert wafer_id != 0

    