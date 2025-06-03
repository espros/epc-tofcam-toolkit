import logging
import numpy as np

import sys
import os
sys.path.insert(0, 'src')

from epc_lib.instruments.tti_supply import PL303
from epc.tofCam660 import TOFcam660
from epc.tofCam660.parser import Frame
import matplotlib.pyplot as plt
import datetime
import time


logging.getLogger("TOFcam660").setLevel(logging.WARNING)

# Create logger
log = logging.getLogger("multi_level_logger")
log.setLevel(logging.DEBUG)  # Capture all levels

# Define a formatter for the log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler_debug = logging.FileHandler("logs/debug.log") 
file_handler_debug.setLevel(logging.DEBUG)
file_handler_debug.setFormatter(formatter)
log.addHandler(file_handler_debug)

file_handler_warning = logging.FileHandler("logs/warning.log") 
file_handler_warning.setLevel(logging.WARNING)
file_handler_warning.setFormatter(formatter)
log.addHandler(file_handler_warning)

file_handler_info = logging.FileHandler("logs/info.log") 
file_handler_info.setLevel(logging.INFO)
file_handler_info.setFormatter(formatter)
log.addHandler(file_handler_info)

# Generate timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
image_counter = 0
image_counter_invalid_total = 0
NUMBER_TEST_LOOPS = 2
POWER_ON_SECONDS = 10 #10 
POWER_OFF_SECONDS = 5 #5
INTEGRATION_TIME_CONFIG_LIST = [
    (250, 10, 1900, 46667)]

# INTEGRATION_TIME_CONFIG_LIST = [
#     (4000, 10, 1900, 46667),
#     (2000, 40, 1900, 43333),
#     (1000, 60, 1900, 41667),
#     (500, 100, 1900, 40750),
#     (250, 100, 1900, 39000),
#     (125, 100, 1900, 37500),
#     (62, 100, 1900, 37500),
#     (31, 150, 1900, 37500),
#     (16, 200, 1900, 37500),
#     (8, 300, 1900, 37500),
#     (4, 350, 1900, 37500),
#     (2, 375, 1900, 37500),
#     (1, 400, 1900, 37500)
# ]

INTEGRATION_TIME_CONFIG_LIST_NOISE_BARRIER_ITERATIONS = 4
#INTEGRATION_TIME_CONFIG_LIST_GATHER_DATA_ITERATIONS = 10
# INTEGRATION_TIME_CONFIG_LIST_TOTAL_ITERATIONS = (INTEGRATION_TIME_CONFIG_LIST_NOISE_BARRIER_ITERATIONS
#                                                  + INTEGRATION_TIME_CONFIG_LIST_GATHER_DATA_ITERATIONS)

INTEGRATION_TIME_CONFIG_LIST_TOTAL_ITERATIONS = len(INTEGRATION_TIME_CONFIG_LIST)

class TofCam660HDRDevice:
    TOFCAM_HDR_SETTING = 0          # 0: off, 1: spatial HDR, 2: temporal HDR
    TOFCAM_BINNING_SETTING = 0      # 0: None, 1: Vertical, 2: Horizontal, 3: Horizontal + Vertical
    TOFCAM_MODULATION_SETTING = 3   # MHz (24, 12, 6, 3, 1.5, 0.75)

    def __init__(self, ip_address: str):
        self.tofcam660 = TOFcam660(ip_address)
        self.tofcam660.initialize()
        self.tofcam660.settings.set_hdr(self.TOFCAM_HDR_SETTING)
        self.tofcam660.settings.set_binning(self.TOFCAM_BINNING_SETTING)
        self.tofcam660.settings.set_modulation(self.TOFCAM_MODULATION_SETTING)
        self.tofcam660.maxDepth = 50000         # 50m
        self.tofcamChipId, self.tofcamWaferId = self.tofcam660.device.get_chip_infos()
        self.tofcamFWVersionString = self.tofcam660.device.get_fw_version()
        #self.tofcamFWVersionDict = self.tofcam660.device.get_fw_version_values()
        #self.has_illuminator_segment_control = self._is_fw_version_greater_than_or_equal(major=3, minor=25)
#        if self.has_illuminator_segment_control:
#            self.tofcam660.settings.set_illuminator_segments(segment_1_on=True, segment_2_on=True, segment_3_on=True, segment_4_on=True)
#        else:
#            log.warning(f"TOFcam660 firmware version ({self.tofcamFWVersionString}) does not support illuminator segment control, all segments always enabled")
        self._hdr = None
        self._hdr_image = None
        self._hdr_raw_measurements = None
        self._invalid_frame_count = 0
        self._image_counter = 0

    def __del__(self):
        log.debug("delete camera device")
        self.tofcam660.__del__()


    def _is_fw_version_greater_than_or_equal(self, major: int, minor: int) -> bool:
        if self.tofcamFWVersionDict['major'] > major:
            return True
        elif self.tofcamFWVersionDict['major'] == major:
            if self.tofcamFWVersionDict['minor'] >= minor:
                return True
        return False

    #def _is_valid_tofcam660_frame(self, frame: Frame, integration_time_config: IntegrationTimeConfig = None) -> bool:
    def _is_valid_tofcam660_frame(self, frame: Frame, integration_time_config = None) -> bool:
        if frame is None:
            log.error("Frame is None")
            return False
        if frame.headerVersion != 2:
            log.error(f"Frame header version mismatch, expected: 1, actual: {frame.headerVersion}")
            return False
        if frame.measurementType != 0:  #  DATA_DISTANCE_AMPLITUDE
            log.error(f"Frame measurement type mismatch, expected: 0 (DATA_DISTANCE_AMPLITUDE), actual: {frame.measurementType}")
            return False
        EXPECTED_SHAPE = (240, 320)
        if frame.rows != EXPECTED_SHAPE[0]:
            log.error(f"Frame height/rows mismatch, expected: {EXPECTED_SHAPE[0]}, actual: {frame.rows}")
            return False
        if frame.cols != EXPECTED_SHAPE[1]:
            log.error(f"Frame width/cols mismatch, expected: {EXPECTED_SHAPE[1]}, actual: {frame.cols}")
            return False
        if frame.leftColumn != 0:
            log.error(f"Frame left column (RoiX0) mismatch, expected: 0, actual: {frame.leftColumn}")
            return False
        if frame.topRow != 0:
            log.error(f"Frame top row (RoiY0) mismatch, expected: 0, actual: {frame.topRow}")
            return False
        if frame.lowIntTime != integration_time_config[0]:
            log.error(f"Frame integration time mismatch, expected: {integration_time_config[0]}, actual: {frame.lowIntTime}")
            return False
        if frame.distance is None:
            log.error("Frame distance is None")
            return False
        if frame.amplitude is None:
            log.error("Frame amplitude is None")
            return False
        if np.shape(frame.distance) != EXPECTED_SHAPE:
            log.error(f"Frame distance shape mismatch, expected: {EXPECTED_SHAPE}, actual: {np.shape(frame.distance)}")
            return False
        if np.shape(frame.amplitude) != EXPECTED_SHAPE:
            log.error(f"Frame amplitude shape mismatch, expected: {EXPECTED_SHAPE}, actual: {np.shape(frame.amplitude)}")
            return False
        # NOTE: Documentation (v3) states hundredths of degrees Celsius (ie. -1234 = -12.34 C); however, already /100 in parser code, so values are float in Celsius
        # valid: -50 to 135 C inclusive (given by Espros for TOFcam635, reused for TOFcam660)
        rounded_temperature_celsius = round(frame.temperature, 2)
        if rounded_temperature_celsius < -50.0 or rounded_temperature_celsius > 135.00:
            log.warning(f"Frame temperature out of range, expected: -50 to 135 C, actual: {rounded_temperature_celsius}")
            return False
        if frame.dcs is not None:
            log.warning("Unexpected DCS data in frame")
            return False

        return True

    def take_measurement(self) -> tuple[bool, int]:
        """Runs the measurement and returns the success status"""
        self._hdr_image = None
        self._hdr_raw_measurements = None

        global image_counter_invalid_total
        #self._invalid_frame_count = 0
        #self._image_counter = 0

        for config_list_iteration in range(INTEGRATION_TIME_CONFIG_LIST_TOTAL_ITERATIONS):
            if config_list_iteration < INTEGRATION_TIME_CONFIG_LIST_NOISE_BARRIER_ITERATIONS:
                build_noise_barrier = True
            else:
                build_noise_barrier = False

            for list_index in range(len(INTEGRATION_TIME_CONFIG_LIST)):
                integration_time_config = INTEGRATION_TIME_CONFIG_LIST[list_index]
                self.tofcam660.settings.set_integration_time(int_time_us=integration_time_config[0])
                self.tofcam660.settings.set_minimal_amplitude(minimum=integration_time_config[1])

                image_index = config_list_iteration * len(INTEGRATION_TIME_CONFIG_LIST) + list_index
                distance_amplitude_frame = None
                IMAGE_FRAME_TRY_COUNT = 1
                try_index = -1
                for try_index in range(IMAGE_FRAME_TRY_COUNT):
                    distance_amplitude_frame = self.tofcam660.get_distance_and_amplitude()
                    crc_bool = self.tofcam660.get_crc_status()
                    self._image_counter += 1
                    
                     # Create subplots
                    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

                    img0 = axes[0].imshow(distance_amplitude_frame[0], vmin=0, vmax=4000)
                    axes[0].set_title("Distance Image")
                    plt.colorbar(img0, ax=axes[0])

                    img1 = axes[1].imshow(distance_amplitude_frame[1], vmin=0, vmax=3000)
                    axes[1].set_title("Amplitude Image")
                    plt.colorbar(img1, ax=axes[1])
                    # Save figure with timestamp
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"plots/{crc_bool}_plot_distAmp_{timestamp}_waferID_{str(self.tofcamWaferId)}_chipID_{str(self.tofcamChipId)}.png"
                    plt.savefig(filename, dpi=300)  # Higher dpi for better resolution
                    plt.close()

                    if self._is_valid_tofcam660_frame(self.tofcam660.frame, integration_time_config):
                        log.info(f"camera acquired image number #: {image_counter} as expected, incorrect images #: {image_counter_invalid_total}")
                        break
                    else:
                        log.warning(f"Invalid frame for image {image_index} (integration time: {integration_time_config[0]} us), "
                                    f" attempt {try_index + 1}/{IMAGE_FRAME_TRY_COUNT}, retrying...")
                        distance_amplitude_frame = None
                        self._invalid_frame_count += 1
                        image_counter_invalid_total+=1

                if distance_amplitude_frame is None:
                    log.error(f"Failed to get valid frame for image {image_index}, measurement failure")
                    return False, self._invalid_frame_count

                #self._hdr.add_measurement(distance_amplitude_frame, integration_time_config, build_noise_barrier, try_index + 1)

        # self._hdr_image = self._hdr.get_hdr_image_uint16()
        # self._hdr_raw_measurements = self._hdr.get_measurements_in_hdr_image()
        return True, self._invalid_frame_count

def main():
    supply = PL303('10.10.32.226')
    print(supply.getId())

    #%%
    supply._CH = 1 # ch2 is on led
    supply._VOLTAGE_MAX = 24
    supply.outputOff(supply._CH)
    supply.setVoltage(supply._CH, supply._VOLTAGE_MAX)
    supply.setCurrentRangeHigh(supply._CH)
    supply.setCurrentLimit(supply._CH, 0.0)
    supply.outputOff(supply._CH)
    
    global image_counter

    #supply.write('OCP{} 3.0'.format(supply._CH)) # set overcurrent protection of CH2 to 1A
    #supply.write('DELTAI{} 0.5'.format(supply._CH))

    for loop in range(NUMBER_TEST_LOOPS):
        image_counter += 1
        if 'camera' in locals() or 'camera' in globals():
            camera.__del__()

        supply.setCurrentRangeHigh(supply._CH)
        supply.setCurrentLimit(supply._CH, 3)
        supply.outputOn(supply._CH)
        
        time.sleep(POWER_ON_SECONDS)

        camera = TofCam660HDRDevice(ip_address='10.10.31.180')
        print(camera.take_measurement())
        camera.__del__()

        supply.outputOff(supply._CH)
        time.sleep(POWER_OFF_SECONDS)


    # Close all handlers
    for handler in log.handlers:
        handler.close()
        
    #add device wafer and chip ID into the log name
    old_name = "logs/debug.log"
    new_name = "logs/"+"waferID_"+str(camera.tofcamWaferId) + "_chipID_"+str(camera.tofcamChipId)+"_"+timestamp+"_debug.log"
    os.rename(old_name, new_name)
    old_name = "logs/warning.log"
    new_name = "logs/"+"waferID_"+str(camera.tofcamWaferId) + "_chipID_"+str(camera.tofcamChipId)+"_"+timestamp+"_warning.log"
    os.rename(old_name, new_name)
    old_name = "logs/info.log"
    new_name = "logs/"+"waferID_"+str(camera.tofcamWaferId) + "_chipID_"+str(camera.tofcamChipId)+"_"+timestamp+"_info.log"
    os.rename(old_name, new_name)

    supply.outputOff(supply._CH)

# Standard Python convention to call main
if __name__ == "__main__":
    main()