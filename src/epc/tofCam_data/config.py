from pathlib import Path

TOFCAM_LIB_BIN = Path(__file__).parent.parent / "tofCam_lib" / "bin"
DATA = Path(__file__).parent.parent / "data"

CrcCalc_linux = TOFCAM_LIB_BIN / "CrcCalc_linux.so"
CrcCalc = TOFCAM_LIB_BIN / "CrcCalc.dll"
CrcCalc_darwin = TOFCAM_LIB_BIN / "CrcCalc_darwin.a"

WIDE_FIELD = DATA/"lense_calibration_wide_field.csv"
NARROW_FIELD = DATA/"lense_calibration_narrow_field.csv"
STANDARD_FIELD = DATA/"lense_calibration_standard_field.csv"