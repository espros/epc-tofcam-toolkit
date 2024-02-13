import numpy as np
import matplotlib.pyplot as plt
from epc.tofCam611.serialInterface import SerialInterface
from epc.tofCam611.camera import Camera

# camera connection
com = SerialInterface('COM3')
camera = Camera(com)

# set camera settings
camera.powerOn()
camera.setIntTime_us(500)  # integration time in µSeconds

# get camera information
productionYear, productionWeek = camera.getProductionDate()
print(f'# camera production date: year {productionYear}, week {productionWeek}')

chipId, waferId = camera.getChipInfo()
print(f'# chipID: {chipId}, waferID: {waferId}')

chipType, device, version = camera.getIdentification()
print(f'# chipType: {chipType}, device: {device}, version: {version}')

fwVersionMajor, fwVersionMinor = camera.getFwRelease()
print(f'# firmware version: V{fwVersionMajor}.{fwVersionMinor}')

chipTemperature = camera.getChipTemperature()
print(f'# chip temperature: {chipTemperature}°C')

# measure
tof_distance = np.array(camera.getDistance())
print('TOF distance image:')
print(np.around(tof_distance, decimals=1))

# plot
plt.imshow(tof_distance)
plt.title('TOF distance image', fontsize=12)
plt.colorbar()
plt.show()