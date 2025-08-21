import logging
import numpy as np
import sys
import os
import datetime
import time
import matplotlib.pyplot as plt

# Insert custom paths
sys.path.insert(0, 'src')
sys.path.insert(0, 'epc_lib')

from epc.tofCam660 import TOFcam660
from epc.tofCam660.parser import Frame

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

protocol = 'UDP'  # Default protocol

# Configure logging to write to a file
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/Test_FPS_{protocol}_{timestamp}.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(f"Test_FPS_{timestamp}")
log.setLevel(logging.INFO)

file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
log.addHandler(file_handler)


NUMBER_FPS_TEST_LOOPS = 50
INTEGRATION_TIME_CONFIG_LIST = [(100, 10, 1900, 46667)]
INTEGRATION_TIME_CONFIG_LIST_NOISE_BARRIER_ITERATIONS = 4
INTEGRATION_TIME_CONFIG_LIST_TOTAL_ITERATIONS = len(INTEGRATION_TIME_CONFIG_LIST)

class TofCam660HDRDevice:
    TOFCAM_HDR_SETTING = 0
    TOFCAM_BINNING_SETTING = 0
    TOFCAM_MODULATION_SETTING = 3

    def __init__(self, ip_address: str):
        self.tofcam660 = TOFcam660(ip_address)
        self.tofcam660.initialize()
        self.tofcam660.settings.set_hdr(self.TOFCAM_HDR_SETTING)
        self.tofcam660.settings.set_binning(self.TOFCAM_BINNING_SETTING)
        self.tofcam660.settings.set_modulation(self.TOFCAM_MODULATION_SETTING)
        self.tofcam660.maxDepth = 50000
        self.tofcamChipId, self.tofcamWaferId = self.tofcam660.device.get_chip_infos()
        self.tofcamFWVersionString = self.tofcam660.device.get_fw_version()
        self._hdr = None
        self._hdr_image = None
        self._hdr_raw_measurements = None
        self._invalid_frame_count = 0
        self._image_counter = 0

    def __del__(self):
        log.debug("delete camera device")
        if self.tofcam660 is not None:
            self.tofcam660.__del__()

    def _is_valid_tofcam660_frame(self, frame: Frame, integration_time_config=None) -> bool:
        if frame is None:
            log.error("Frame is None")
            return False
        # [Validation checks omitted for brevity — keep yours as-is]
        return True

    def take_measurement(self) -> float:
        self.tofcam660.settings.set_integration_hdr(INTEGRATION_TIME_CONFIG_LIST[0])
        self.tofcam660.device.set_data_transfer_protocol(protocol)
        self.tofcam660.settings.set_hdr(self.TOFCAM_HDR_SETTING)
        FW_version = self.tofcam660.device.get_fw_version()
        self.tofcam660.settings.captureMode=0  # Set capture mode stream
        #self.tofcam660.settings.set_flex_mod_freq(3)
        frame_times = []
        for frame in range(100):
            t0 = time.perf_counter()
            self.tofcam660.get_distance_and_amplitude()
            #self.tofcam660.get_raw_dcs_images()
            t1 = time.perf_counter()
            frame_times.append(t1 - t0)

        fps_list = [1 / t for t in frame_times]
        fps = sum(fps_list) / len(fps_list)
        log.info(f"fw version: {FW_version} protocol: {protocol} FPS: {fps:.2f} for {NUMBER_FPS_TEST_LOOPS} frames")

        plt.figure(figsize=(10, 5))
        plt.plot(fps_list, label='FPS per frame')
        plt.xlabel('Frame Number')
        plt.ylabel('FPS')
        plt.title(f'FPS over {NUMBER_FPS_TEST_LOOPS} frames, protocol: {protocol}, FW: {FW_version}')
        plt.legend()
        plt.grid()
        plt.savefig(f"logs/FPS_plot_{protocol}_{timestamp}.png")
        self.tofcam660.settings.captureMode=0  # Set capture mode stream
        #self.tofcam660.get_raw_dcs_images()
        self.tofcam660.get_distance_and_amplitude()
        return fps


def main():
    camera = TofCam660HDRDevice(ip_address='10.10.31.180')
    fps = camera.take_measurement()
    print(f"FPS: {fps:.2f} for {NUMBER_FPS_TEST_LOOPS} frames")
    camera.tofcam660.device.set_data_transfer_protocol('UDP')
    del camera

if __name__ == "__main__":
    main()
