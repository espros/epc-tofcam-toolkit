from pathlib import Path

EPC_LOGO = Path(__file__).parent / "icons" / "epc-logo.png"
TOFCAM_LIB_BIN = Path(__file__).parent.parent / "tofCam_lib" / "bin"
DATA = Path(__file__).parent.parent / "data"

CrcCalc_linux = TOFCAM_LIB_BIN / "CrcCalc_linux.so"
CrcCalc = TOFCAM_LIB_BIN / "CrcCalc.dll"
CrcCalc_darwin = TOFCAM_LIB_BIN / "CrcCalc_darwin.a"

NARROW_FIELD     = DATA/"lens_calibration_narrow_field_p100596.csv"
STANDARD_FIELD   = DATA/"lens_calibration_standard_field_p100843.csv"
WIDE_FIELD       = DATA/"lens_calibration_wide_field_p100506.csv"
WIDE_WIDE_FIELD  = DATA/"lens_calibration_wide_wide_field_p101152.csv"
ULTRA_WIDE_FIELD = DATA/"lens_calibration_ultra_wide_field_p101156.csv"


if __name__ == "__main__":

    with open(NARROW_FIELD, "r") as f:
        x = f.read()
        print(x)

    with open(STANDARD_FIELD, "r") as f:
        x = f.read()
        print(x)

    with open(WIDE_FIELD, "r") as f:
        x = f.read()
        print(x)

    with open(WIDE_WIDE_FIELD, "r") as f:
        x = f.read()
        print(x)

    with open(ULTRA_WIDE_FIELD, "r") as f:
        x = f.read()
        print(x)

    # with open(CrcCalc_linux, "rb") as f:
    #     x = f.read()

    with open(CrcCalc, "rb") as f:
        f.read()

    # with open(CrcCalc_darwin, "rb") as f:
    #     x = f.read()

    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image
    im = Image.open(EPC_LOGO)
    data = np.array(im)
    plt.imshow(data)  # shows a bluish image of the logo
    plt.show()
