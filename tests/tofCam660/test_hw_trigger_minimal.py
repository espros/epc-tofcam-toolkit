
import sys

from epc.tofCam660.interface import DataType

# Insert custom paths
sys.path.insert(0, 'src')
sys.path.insert(0, 'epc_lib')

from epc.tofCam660 import TOFcam660
def main():
    # Step 1: Initialize the Python API and Ethernet interface
    # place this in system initialization or sensor power-up sequence
    camera = TOFcam660(ip_address='10.10.31.180')

    # Enable rolling mode & configure other camera settings here
    camera.settings.set_rolling_mode("1DCS")

    # Step 2: Receive data through HW trigger
    # place this in the part of where data processing happens
    print("----------- Waiting for HW trigger -------------")

    # Camera will send distance images with default settings
    camera.settings.set_hw_trigger_data_type(DataType.DISTANCE) 
    frame_count = 100
    for frame in range(100):
        d = camera.get_hw_trigger_image()
        assert d.shape == (240, 320), "Distance image shape mismatch"

    print(f"--------------Acquisition of {frame_count} frames finished----------")

    # Step 3: Clean-up sequence
    # place this in your system power-down sequence
    del camera

if __name__ == "__main__":
    main()