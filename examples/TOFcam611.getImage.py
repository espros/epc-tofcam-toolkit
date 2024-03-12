import matplotlib.pyplot as plt
from epc.tofCam611.camera import Camera as TOFCam611
from epc.tofCam611.serialInterface import SerialInterface

# setup the camera
cam = TOFCam611(SerialInterface())

# print chip information
chipID, waferID = cam.getChipInfo()
print(f'Chip ID: {chipID}')
print(f'Wafer ID: {waferID}')

# get distance image
distance = cam.getDistance()

# add your own code here to process the distance image
...

# plot the distance image
plt.imshow(distance, cmap='turbo', vmin=0, vmax=5000)
plt.axis('off')
plt.title('TOFcam611 - Distance Image')
plt.colorbar()
plt.show()