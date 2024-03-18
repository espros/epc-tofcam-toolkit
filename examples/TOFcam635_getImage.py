import matplotlib.pyplot as plt
from epc.tofCam635 import TOFcam635

# setup the camera
cam = TOFcam635()
cam.initialize()

# print chip information
chipID, waferID = cam.device.get_chip_infos()
print(f'Chip ID: {chipID}')
print(f'Wafer ID: {waferID}')

# change some settings
cam.settings.set_integration_time(125)

# get distance image
distance = cam.get_distance_image()

# add your own code here to process the distance image
...

# plot the distance image
plt.imshow(distance, cmap='turbo', vmin=0, vmax=5000)
plt.axis('off')
plt.title('TOFcam635 - Distance Image')
plt.colorbar()
plt.show()