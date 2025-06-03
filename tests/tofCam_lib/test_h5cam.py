import pytest


def test_h5cam():
    from pathlib import Path

    import numpy as np

    from epc.tofCam_lib.h5Cam import H5Cam
    source_path = Path(__file__).parent.parent / "data" / "amplitude_w544c005_250527_134627.h5"
    cam = H5Cam(source=source_path, continuous=True)
    assert len(cam) > 0
    __index = cam.index

    with pytest.raises(ValueError):
        cam.get_distance_image()
    with pytest.raises(ValueError):
        cam.get_raw_dcs_images()
    with pytest.raises(ValueError):
        cam.get_point_cloud()
    with pytest.raises(ValueError):
        cam.get_grayscale_image()

    _frame = cam.get_amplitude_image()
    assert isinstance(_frame, np.ndarray)
    assert len(_frame) > 0
    assert __index == cam.index - 1
