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