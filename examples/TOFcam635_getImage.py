import matplotlib.pyplot as plt
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