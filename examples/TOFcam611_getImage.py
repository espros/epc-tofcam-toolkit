import matplotlib.pyplot as plt
from epc.tofCam611 import TOFcam611
import time

# setup the camera
cam = TOFcam611()
cam.initialize()

# change some settings
cam.settings.set_integration_time(50)

# get distance image
distance = cam.get_distance_image()

# add your own code here to process the distance image
...

# plot the distance image
plt.imshow(distance, cmap='turbo', vmin=0, vmax=5000)
plt.axis('off')
plt.title('TOFcam611 - Distance Image')
plt.colorbar()
plt.show()