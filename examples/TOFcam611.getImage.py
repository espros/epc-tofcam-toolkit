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