import numpy as np
import h5py
import datetime
import time
from epc.tofCam660 import TOFcam660
import logging
from collections import deque

logger = logging.getLogger("calibrate_drnu")

# ESTABLISH CONNECTION
camera = TOFcam660()
camera.initialize()
camera.settings.set_hdr(0)

# CALIBRATION PARAMETER
waferID_chipID = camera.device.get_chip_infos()
MOD_FREQ_MHZ = 12
MAX_ALLOWED_TEMP_STD = 0.21 # max allowed std before calibration starts
MAX_ALLOWED_TEMP_DEVIATION = 1.5 # max allowed deviation during calibration
AMPLITUDE_TARGET_DN = 1000
N_FRAMES_PER_STEP = 50
ROI = {'x1': 150, 'x2': 170, 'y1': 110, 'y2': 130}

# CAMERA SETTINGS
camera.settings.set_minimal_amplitude(100)
camera.settings.set_modulation(MOD_FREQ_MHZ, 0)

def calc_amplitude(cx:np.ndarray, cy: np.ndarray):
    return np.sqrt(cx.astype(float)**2 + cy.astype(float)**2)

def calc_distance(cx:np.ndarray, cy: np.ndarray, modFreq: float):
    C = 299792458
    phi = np.arctan2(cy, cx)
    return 1000 * phi * C / (4*np.pi*modFreq) # distance in mm

def get_distance_amplitude(dcs: np.ndarray):
    cx = dcs[0] - dcs[2]
    cy = dcs[1] - dcs[3]
    
    amp = calc_amplitude(cx, cy)
    dist = calc_distance(cx, cy, MOD_FREQ_MHZ*1000000)
    return (dist, amp) 

def find_tof_integration_time_us():
    int_time_us = 50
    error = 100
    while np.abs(error) > 50:
        camera.settings.set_integration_time(int_time_us)
        dcs = camera.get_raw_dcs_images()
        _, amplitude = get_distance_amplitude(dcs)

        mean_amp = np.mean(amplitude)
        error = AMPLITUDE_TARGET_DN - mean_amp
        int_time_us += int(int_time_us * error / AMPLITUDE_TARGET_DN)
    return int_time_us, int(mean_amp)

def find_calibration_temperature():
    N_SAMPLES = 40
    temperatures = deque(maxlen=N_SAMPLES)
    logger.info('warmpup camera')
    for _ in range(100):
        camera.get_raw_dcs_images()
        temperatures.append(camera.device.get_chip_temperature())
        temp_std = np.std(temperatures)
        print(f"std over {N_SAMPLES} samples: {temp_std:04.3f}°C. Current temperature: {np.mean(temperatures):04.3f}°C\r", end="")

    logger.info('wait for temperature to stabilize')
    while temp_std > MAX_ALLOWED_TEMP_STD:
        camera.get_raw_dcs_images()
        temperatures.append(camera.device.get_chip_temperature())
        temp_std = np.std(temperatures)

        print(f"std over {N_SAMPLES} samples: {temp_std:04.3f}°C. Current temperature: {np.mean(temperatures):04.3f}°C\r", end="")
    return np.mean(temperatures)

def set_calibration_temperature():
    def get_temperature_diff():
        camera.get_grayscale_image() # get a grayscale image to update the temperature
        temp = camera.device.get_chip_temperature()
        return np.abs(temp - temperature_target_for_calibration_deg)

    temp_diff = get_temperature_diff() # max allowed std before calibration starts
    while temp_diff > MAX_ALLOWED_TEMP_DEVIATION: # max allowed deviation during calibration
        if temp_diff > 0:
            logger.info(f"cool down. Temperature difference: {temp_diff:04.3f} deg")
            time.sleep(15)
        else:
            logger.info(f"heat up. Temperature difference: {temp_diff:04.3f} deg")
            for i in range(50):
                camera.get_raw_dcs_images()
        temp_diff = get_temperature_diff()

def cound_needed_dll_steps():
    camera.settings.set_dll_step(0)
    distance_per_dll_step = np.empty(50)

    for dll_step in range(50):
        camera.settings.set_dll_step(dll_step)
        dcs = camera.get_raw_dcs_images()
        distance = get_distance_amplitude(dcs)[0]
        distance_per_dll_step[dll_step] = np.mean(distance[ROI['x1']:ROI['x2'],ROI['y1']:ROI['y2']])

    first, second = np.where(distance_per_dll_step<=np.sort(distance_per_dll_step)[1])[0]

    return second - first

def calibrate():
    camera.settings.set_dll_step(0)
    for dll_step in np.arange(dll_steps_needed):
        camera.settings.set_dll_step(dll_step)
        set_calibration_temperature()
        temperature_now_deg = camera.device.get_chip_temperature()
        logger.info(f"dll step: {dll_step}, temperature: {temperature_now_deg:03.1f} deg")
        for frame in np.arange(N_FRAMES_PER_STEP):
            distance, amplitude = get_distance_amplitude(camera.get_raw_dcs_images())
            calibration_distance_mm[:,:,frame, dll_step] = distance[ROI['y1']:ROI['y2'], ROI['x1']:ROI['x2']]
            calibration_amplitude_dn[:,:,frame, dll_step] = amplitude[ROI['y1']:ROI['y2'], ROI['x1']:ROI['x2']]
            calibration_temperature_deg[frame, dll_step] = camera.device.get_chip_temperature()
        logger.info(f'distance at dll step {dll_step}: {np.mean(calibration_distance_mm[:,:,0, dll_step]):04.3f} mm')

def save_calibration_to_file():
    # Get the current date
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y%m%d_%H%M")

    # Create an h5 file
    filename = f'scripts/data/{formatted_date}_calibration_{MOD_FREQ_MHZ}MHz.h5'
    with h5py.File(filename, 'w') as f:
        group = f.create_group('data')
        group.create_dataset('waferID_chipID', data=waferID_chipID)
        group.create_dataset('distance', data=calibration_distance_mm)
        group.create_dataset('amplitude', data=calibration_amplitude_dn)
        group.create_dataset('temperature', data=calibration_temperature_deg)
        group.create_dataset('calibration_temperature', data=temperature_target_for_calibration_deg)
        group.create_dataset('modulation_frequency', data=MOD_FREQ_MHZ)

    return filename

# CALIBRATION SCRIPT
logger.info(f"\n{'start calibration'}\n{'='*30}")
logger.info(f"wafer ID: {waferID_chipID[0]}, chip ID: {waferID_chipID[1]}")

integration_time_tof_us, mean_amp = find_tof_integration_time_us()
logger.info(f"integration time for {mean_amp} dn: {integration_time_tof_us} us")

logger.info(f"find calibration temperature: target std < {MAX_ALLOWED_TEMP_STD} deg")
temperature_target_for_calibration_deg =  find_calibration_temperature()
logger.info(f"calibration temperature is at: {temperature_target_for_calibration_deg:03.1f} deg")

dll_steps_needed = 42 #int(cound_needed_dll_steps())
logger.info(f"needed dll steps: {dll_steps_needed}")

logger.info(f"capture calibration data:")

# PREPARE ARRAY's FOR CALIBRATION DATA
calibration_distance_mm =  np.empty((ROI['x2']-ROI['x1'], ROI['y2']-ROI['y1'], N_FRAMES_PER_STEP, dll_steps_needed))
calibration_amplitude_dn =  np.empty((ROI['x2']-ROI['x1'], ROI['y2']-ROI['y1'], N_FRAMES_PER_STEP, dll_steps_needed ))
calibration_temperature_deg =  np.empty((N_FRAMES_PER_STEP, dll_steps_needed))
calibrate()

filename = save_calibration_to_file()
logger.info(f"calibration successfully saved: {filename}")
logger.info(f"distance array shape: {calibration_distance_mm.shape}")
logger.info(f"ampitude array shape: {calibration_amplitude_dn.shape}")
logger.info(f"temperature array shape: {calibration_temperature_deg.shape}")
