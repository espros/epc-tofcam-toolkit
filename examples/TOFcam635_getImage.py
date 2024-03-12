import matplotlib.pyplot as plt
from epc.tofCam635 import TofCam635

# setup the camera
cam = TofCam635()

# print chip information
chipID, waferID = cam.cmd.getChipInfo()
print(f'Chip ID: {chipID}')
print(f'Wafer ID: {waferID}')

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