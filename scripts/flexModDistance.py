import numpy as np
import matplotlib.pyplot as plt
from epc.tofCam660 import TOFcam660
import logging
import time

MAX_DCS_VALUE = 64000
C = 299792458
TOF_COS_DISTANCE_CHIP_TO_FRONT = 28.0
TOF_COS_CALIBRATION_BOX_LENGTH = 330.0
TOF_COS_TEMPERATURE_COEFFICIENT = 12.9 + 4.6

CONST_OFFSET_CORRECTION = TOF_COS_CALIBRATION_BOX_LENGTH-TOF_COS_DISTANCE_CHIP_TO_FRONT - 7/8*12500

DEFAULT_MOD_FREQ = 24
DEFAULT_MOD_CHANNEL = 0
DEFAULT_INT_TIME = 500
DEFAULT_MIN_AMPLITUDE = 100

DEFAULT_FLEX_MOD_FREQ = 16E6


def get_distance_amplitude_dcs(cam: TOFcam660, calibData: dict, modFreq_MHz: int, int_time_us):
    logging.info(f"get image with modulation frequency {modFreq_MHz} MHz and integration time {int_time_us} us")

    # prepare camera settings to calibrated temperature
    # Could be handled in the camera firmware but for now we do it here
    cam.settings.set_integration_time(0)
    cam.settings.set_modulation(calibData['modulation(MHz)'], 0)
    cam.get_distance_and_amplitude()

    # adjust integration time relative to calibrated modulation frequency
    # Could be handled in the camera firmware but for now we do it here
    adjusted_int_time_us = int_time_us * (modFreq_MHz / calibData['modulation(MHz)'])
    cam.settings.set_integration_time(int(adjusted_int_time_us))

    # get dcs at frequency
    cam.settings.set_flex_mod_freq(modFreq_MHz, delay=0.01)
    dcs = cam.get_raw_dcs_images()
    # dcs = cam.get_raw_dcs_images()
    temp = cam.device.get_chip_temperature()

    # filter invalid values
    dcs = dcs.astype(np.float32)
    dcs[dcs >= MAX_DCS_VALUE] = np.nan

    # calculate amplitude
    diff0 = dcs[2] - dcs[0]
    diff1 = dcs[3] - dcs[1]
    amplitude = np.sqrt(diff0**2 + diff1**2) / 2

    # calculate phase
    phi = np.arctan2(diff1, diff0) + np.pi
    # phi[amplitude < DEFAULT_MIN_AMPLITUDE] = np.nan 

    # calculate distance
    unambiguity_mm = (C / (2 * modFreq_MHz * 1E6)) * 1000
    distance = (phi * unambiguity_mm) / (2 * np.pi)

    # compensate offsets
    temp_offset = (calibData['calibrated_temperature(mDeg)']/1000 - temp) * TOF_COS_TEMPERATURE_COEFFICIENT
    distance = distance + (6250 - calibData['atan_offset']) + temp_offset + CONST_OFFSET_CORRECTION
    
    distance %= unambiguity_mm    # handle unambiguity steps

    return (distance, amplitude, dcs)


def main():
    # initialization sequence
    cam = TOFcam660()
    cam.initialize()
    cam.settings.set_minimal_amplitude(DEFAULT_MIN_AMPLITUDE)
    cam.settings.disable_filters()
    cam.settings.set_modulation(DEFAULT_MOD_FREQ, DEFAULT_MOD_CHANNEL)
    cam.settings.set_binning(0)
    cam.settings.set_hdr(0)
    cam.settings.set_integration_time(DEFAULT_INT_TIME)

    # get calibration data
    calibData = cam.device.get_calibration_data()
    calibData24Mhz = next((item for item in calibData if item['modulation(MHz)'] == 24), None)
    assert calibData24Mhz is not None, "Calibration data for 24 MHz not found"

    # get normal distance and amplitude image
    cam.settings.set_modulation(24, 0)
    cam.settings.set_integration_time(300)
    distance_norm, amplitude_norm = cam.get_distance_and_amplitude()

    # get flexmod distance, amplitude and dcs
    distance, amplitude, dcs = get_distance_amplitude_dcs(cam, calibData24Mhz, modFreq_MHz=18, int_time_us=300)

    plt.figure(figsize=(10, 5))
    plt.subplot(2, 2, 1)
    plt.title('Amplitude flexMod')
    plt.imshow(amplitude , cmap='turbo', vmin=0, vmax=3200)
    plt.colorbar(label='Amplitude (DN)')

    plt.subplot(2, 2, 2)
    plt.title('Amplitude normal')
    plt.imshow(amplitude_norm, cmap='turbo', vmin=0, vmax=3200)
    plt.colorbar(label='Amplitude (DN)')

    plt.subplot(2, 2, 3)
    plt.title('Distance flexMod')
    plt.imshow(distance, cmap='turbo', vmin=0, vmax=5000)
    plt.colorbar(label='Distance (mm)')

    plt.subplot(2, 2, 4)
    plt.title('Distance normal')
    plt.imshow(distance_norm, cmap='turbo', vmin=0, vmax=5000)
    plt.colorbar(label='Distance (mm)')

    plt.show()



if __name__ == "__main__":
    main()