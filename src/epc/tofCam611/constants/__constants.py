from . import __epc611
from . import __mode
from . import __modFrequency

VERSION=2.3


# needs to be defined before calibration gets called
TOFFRAME_EVAL_PATH = 'calibrationData/TOF_frame'
TOFRANGE_EVAL_PATH = 'calibrationData/TOF_range'
# TOFRANGE_EVAL_PATH = '//srv-emme.ch.epc/Products/03_Modules_Standard/TOF_range_611/2_Production/03_Test-Results_Statistics/Calibration_new/'
# TOFFRAME_EVAL_PATH = '//srv-emme.ch.epc/Products/03_Modules_Standard/TOF_frame_611/2_Production/03_Test-Results_Statistics/Calibration_new/'


LAST_PLOTTED_PATH = '' # path to put figures from plotly in it
LAST_MEAS_PATH = 'lastMeasurements/'   # path to put last measurements, stage measurements
TOFFRAME_PLOT_PATH = TOFFRAME_EVAL_PATH+LAST_PLOTTED_PATH
TOFRANGE_PLOT_PATH = TOFRANGE_EVAL_PATH+LAST_PLOTTED_PATH
TOFFRAME_MEAS_PATH = TOFFRAME_EVAL_PATH+LAST_MEAS_PATH
TOFRANGE_MEAS_PATH = TOFRANGE_EVAL_PATH+LAST_MEAS_PATH

from . import __calibration
TOF_FRAME_STRING = 'TOF_frame611'
TOF_RANGE_STRING = 'TOF_range611'


MAX_INTEGRATION_TIME = 2**16-1
MAX_INTEGRATION_TIME_US = 1600
MIN_INTEGRATION_TIME_US = 10

DEVICE_TOFFRAME = 1
DEVICE_TOFRANGE = 0

DLL_STEP_0 = 0 #usuall set dll step to operate from 2



FPS_DELAY = 0.035
CONVERT_TO_MM = 10
CONVERT_TO_DEGREE = 100
epc611 = __epc611
calibration = __calibration
modFrequency = __modFrequency
mode = __mode
