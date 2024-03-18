# TOFcam modules

You can use the TOFcam modules to run your own scripts. 
Here are three examples for how you could start. 

## TOFcam660
```python
import matplotlib.pyplot as plt
from epc.tofCam660 import Server as TOFCam660
from epc.tofCam660.epc660 import Epc660Ethernet
# setup the camera
epc = Epc660Ethernet(ip_address='10.10.31.180')
cam = TOFCam660(epc)
# print chip information
chipId = cam.getChipId()
waferId = cam.getWaferId()
print(f'Chip ID: {chipId}')
print(f'Wafer ID: {waferId}')
# get distance image
distance = cam.getTofDistance()[0]
# add your own code here to process the distance image
...
plt.imshow(distance, cmap='turbo', vmin=0, vmax=30000)
plt.colorbar()
plt.show()
```

## TOFcam635
```python
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
```

## TOFcam611
```python
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
```