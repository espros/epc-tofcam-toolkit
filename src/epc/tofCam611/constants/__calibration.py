from . import __writeCalibrationData
from . import __constants as Const


VERSION = 0x0102            # Version of calibration algorithm
COMPENSATION_ENABLED = True             # enable compensation mode on firmware
COMPENSATION_DISABLED = False           # disable compensation mode on firmware
COMPENSATION_SIZE_20MHZ_TOFRANGE = 0x1a # compensation data length for 20Mhz TofRange
COMPENSATION_SIZE_20MHZ_TOFFRAME = 0x1a  # compensation data length for 20Mhz TofFrame
COMPENSATION_RELEVANT_SIZE_20MHZ_TOFFRAME = 0x0a  # get only 10 dll steps because TofFrame operates only to 2m
COMPENSATION_FLASH_SIZE_20MHZ_TOFFRAME = 0x1a  # get only 10 dll steps because TofFrame operates only to 2m

COMPENSATION_BOX_LENGTH = 1500          # compensation box length = 150mm [0.1mm resolution] @0.1mm
COMPENSATION_SIZE_10MHZ_TOFRANGE = 0x32 # compensation data length for 10Mhz TofRange
COMPENSATION_DATA_20MHZ_START_IDX= 6    # start index of 20Mhz data in compensation data of TofFrame
COMPENSATION_DATA_10MHZ_START_IDX= 36   # start index of 10Mhz data in compensation data of TofRange
COMPENSATION_TEMPERATURE_DELTA = 1      # difference in degree what is allowed to change during calibration
FIX_PATTERN_NOISE_DLL_STEP = 3          # dll step where to squeeze error data to eliminate fix pattern noise   
DLL_STEP_THRESHOLD = 200                # threshold for detecting correct dll step @0.1mm
DLL_STEP_MIN_TOLERANCE = 300
DLL_STEP_MAX_TOLERANCE = 340
MAX_FIX_DISTANCE = 15000                # max fix distance for device at 10Mhz  @0.1mm
PHASE_SHIFT_THRESHOLD = 5000            # used for eliminating phase shift, all values below added max distance @0.1mm
CONVERT_TO_MM = 10            # convert from 0.1mm to mm
  
T_INT_RANGE_MIN = 100
T_INT_FRAME_MIN = 200
T_INT_RANGE_10MHZ_MAX = 600
T_INT_RANGE_20MHZ_MAX = 800
T_INT_FRAME_MAX = 650
A_DIFF_FRAME_MAX = 500





writeCalibrationData = __writeCalibrationData

AMPLITUDE_TOFFRAME_OPTIMUM = 1000
AMPLITUDE_TOFFRAME_DELTA   = 50
AMPLITUDE_TOFRANGE_OPTIMUM = 35000
AMPLITUDE_TOFRANGE_DELTA   = 1000
AMPLITUDE_NBF_OPTIMUM = 5000
AMPLITUDE_NBF_DELTA   = 200
AMPLITUDE_TOFRANGE_MIN = 30000
AMPLITUDE_TOFFRAME_MIN = 800

AMPLITUDE_SEARCH_TIMEOUT = 60

CALIBRATION_FOLDER = ''
TOFFRAME_CALIBRATION_PATH = Const.TOFFRAME_EVAL_PATH + CALIBRATION_FOLDER
TOFRANGE_CALIBRATION_PATH = Const.TOFRANGE_EVAL_PATH + CALIBRATION_FOLDER

