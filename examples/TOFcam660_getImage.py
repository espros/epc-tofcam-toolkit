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