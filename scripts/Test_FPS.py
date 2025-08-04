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

# Configure logging to write to a file
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/Test_FPS_{timestamp}.log"

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


NUMBER_FPS_TEST_LOOPS = 100
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
        start = time.perf_counter()
        self.tofcam660.settings.set_integration_hdr(INTEGRATION_TIME_CONFIG_LIST[0])
        self.tofcam660.device.set_data_transfer_protocol('TCP')
        self.tofcam660.settings.set_hdr(self.TOFCAM_HDR_SETTING)
        for frame in range(NUMBER_FPS_TEST_LOOPS):
            # Alternate protocol every frame
            # data_protocol = 'TCP' if frame % 2 == 0 else 'UDP'
            # self.tofcam660.device.set_data_transfer_protocol(data_protocol)
            self.tofcam660.get_distance_and_amplitude()
            # log.info(f"Frame {frame}: Protocol={data_protocol}")

        end = time.perf_counter()
        fps = NUMBER_FPS_TEST_LOOPS / (end - start)
        log.info(f"Alternating protocol FPS: {fps:.2f} for {NUMBER_FPS_TEST_LOOPS} frames")
        return fps


def main():
    camera = TofCam660HDRDevice(ip_address='10.10.31.180')
    fps = camera.take_measurement()
    print(f"FPS: {fps:.2f} for {NUMBER_FPS_TEST_LOOPS} frames")
    camera.tofcam660.device.set_data_transfer_protocol('UDP')
    del camera

if __name__ == "__main__":
    main()
