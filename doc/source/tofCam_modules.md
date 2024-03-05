# TOFcam modules

You can use the TOFcam modules to run your own scripts. 
Here are three examples for how you could start. 

## TOFcam660
```python
import matplotlib.pyplot as plt
from epc.tofCam660 import Server as TOFCam660
from epc.tofCam660.epc660 import Epc660Ethernet

epc = Epc660Ethernet(ip_address='10.10.31.180')
cam = TOFCam660(epc)
chipId = cam.getChipId()
waferId = cam.getWaferId()

print(f'Chip ID: {chipId}')
print(f'Wafer ID: {waferId}')

distance = cam.getTofDistance()[0]
distance[distance > 14000] = 0

plt.imshow(distance, cmap='turbo')
plt.colorbar()
plt.show()
```

## TOFcam635
```python
from epc.tofCam635 import TofCam635

cam = TofCam635()

waferID = cam.get_wafer_id()
chipID = cam.get_chip_id()
print(f'Chip ID: {chipID}')
print(f'Wafer ID: {waferID}')

distance = cam.get_distance_image()

plt.imshow(distance, cmap='turbo')
plt.colorbar()
plt.show()
```

## TOFcam611
```python
import matplotlib.pyplot as plt
from epc.tofCam611.camera import Camera as TOFCam611

cam = TOFCam611()
waferID = cam.get_wafer_id()
chipID = cam.get_chip_id()
print(f'Chip ID: {chipID}')
print(f'Wafer ID: {waferID}')

distance = cam.getDistance()
plt.imshow(distance, cmap='turbo')
plt.colorbar()
plt.show()
```