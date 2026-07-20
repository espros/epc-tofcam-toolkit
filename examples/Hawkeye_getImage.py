import matplotlib.pyplot as plt
from epc.hawkeyeBt.hawkeyeBt import HawkeyeBt
import numpy as np

# adapt this address to your devices MAC address
MAC_ADDRESS = "10:51:DB:28:28:9C"

# setup the camera
with HawkeyeBt(mac_address=MAC_ADDRESS) as hawkeye:
    hawkeye.bt_cam.connect()
    hawkeye.initialize()

    # print chip information
    chipId, waferId = hawkeye.device.get_chip_infos()
    print(f'Chip ID: {chipId}')
    print(f'Wafer ID: {waferId}')

    # change some settings
    hawkeye.settings.set_integration_time(int_time_us=200)
    hawkeye.settings.set_modulation(frequency_mhz=10)
    hawkeye.settings.set_roi((50, 0, 109, 59))

    # get distance image
    image = hawkeye.get_distance_image()

    # add your own code here to process the distance image
    ...

    plt.imshow(image, cmap='turbo')
    plt.colorbar()
    plt.show()