import matplotlib.pyplot as plt
from epc.tofCam660 import TOFcam660

# setup the camera
cam = TOFcam660()
cam.initialize()

# print chip information
chipId, waferId = cam.device.get_chip_infos()
print(f'Chip ID: {chipId}')
print(f'Wafer ID: {waferId}')

# change some settings
cam.settings.set_modulation(frequency_mhz=12)

# get distance image
distance = cam.get_distance_image()

# add your own code here to process the distance image
...

plt.imshow(distance, cmap='turbo', vmin=0, vmax=30000)
plt.colorbar()
plt.show()