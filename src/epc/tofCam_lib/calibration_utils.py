import logging
import time
from collections import deque
from typing import Optional, Tuple

import numpy as np

from epc.tofCam_lib import TOFcam
from epc.tofCam_lib.algorithms import *

logger = logging.getLogger("utils")

MAX_ALLOWED_TEMP_DEVIATION = 0.5  # max allowed deviation during calibration


def find_int_time_for_mean_amplitude(cam: TOFcam, target_amplitude: int, max_deviation=50) -> Tuple[int, float]:
    """
    Find the integration time for a given target amplitude by iteratively adjusting the integration time
    until the mean amplitude is within the specified deviation from the target.

    Args:
        cam: TOFcam instance
        target_amplitude: Target amplitude to achieve
        max_deviation: Maximum allowed deviation from the target amplitude

    Returns:
        int_time_us: Integration time in microseconds that achieves the target amplitude
        mean_amp: Mean amplitude achieved with that integration time
    """
    error = max_deviation + 1  # Initialize error to be larger than max_deviation
    int_time_us = 50  # Start with a low initial integration time

    while (np.abs(error) > max_deviation):
        cam.settings.set_integration_time(int_time_us)
        dcs = cam.get_raw_dcs_images()
        cx, cy = diff_dcs(dcs)
        amplitude = calc_amplitude(cx, cy)

        mean_amplitude = np.mean(amplitude)
        error = target_amplitude - mean_amplitude
        int_time_us += int(int_time_us * error / target_amplitude)
        print(
            f"Integration time: {int_time_us} us, Mean amplitude: {mean_amplitude}, Error: {error}\r", end="")

    return int_time_us, float(mean_amplitude)


def find_stable_temperature(cam: TOFcam, n_samples_to_average=10, max_slope=0.001) -> float:
    """Find a stable running temperature by continuously capturing grayscale images until the temperature stabilizes.
    The temperature is considered stable when the slope of the temperature change is below a specified threshold.
    The user of this function is responsible for setting the correct integration time before calling this function.

    Args:
        cam (TOFcam): TOFcam instance 
        n_samples_to_average (int, optional): Number of samples to use for calculating the slope of the temperature change
        max_slope (float, optional): Maximum allowed slope for the temperature change to be considered stable

    Returns:
        float: Mean value of the `n_samples_to_average` temperature readings
    """
    temperatures: deque[float] = deque(maxlen=n_samples_to_average)
    logger.info('Warming up camera...')
    nFrames = max(n_samples_to_average, 100)
    cam.settings.set_integration_time_grayscale(1000)
    for i in range(nFrames):
        cam.get_raw_dcs_images()
        # Some cameras need a grayscale image to update the temperature
        cam.get_grayscale_image()
        temperatures.append(cam.device.get_chip_temperature())
        print(
            f"Current frame: {i}/{nFrames}, temperature: {np.mean(temperatures):04.3f}°C\r", end="")

    slope = max_slope + 1  # Initialize slope to be larger than max_slope
    logger.info(f"wait for temperature to stabilize")
    while (slope > max_slope):
        cam.get_raw_dcs_images()
        cam.get_grayscale_image()
        temperatures.append(cam.device.get_chip_temperature())
        slope = np.polyfit(np.arange(len(temperatures)), temperatures, 1)[0]
        print(
            f"slope over {n_samples_to_average} samples: {slope:04.3f}°C/sample. Current temperature: {np.mean(temperatures):04.3f}°C", end="\r")

    return float(np.mean(temperatures))


def get_needed_dll_steps_for_wraparound(cam: TOFcam, modulation_freq_hz: int, roi: Optional[Tuple] = None) -> int:
    """ Get the number of steps needed to wrap around the unambiguity range of the camera.
    This is done by iterating through the DLL steps and calculating the distance for each step.

    Args:
        cam (TOFcam): TOFcam instance
        modulation_freq_hz (float): Modulation frequency in Hz

    Returns:
        int: Number of steps needed to wrap around the unambiguity range
    """
    MAX_DLL_STEPS = 50
    distances = np.empty(MAX_DLL_STEPS)
    for i in range(MAX_DLL_STEPS):
        cam.settings.set_dll_step(i)
        dcs = cam.get_raw_dcs_images()
        cx, cy = diff_dcs(dcs)
        distance = calc_distance(cx, cy, modulation_freq_hz)
        distances[i] = distance.mean()
        print(
            f"DLL step: {i}, Distance: {distances[i]:.2f} mm\r", end="")

    # remove outliers at the unambiguity distance
    step_sizes = np.diff(distances)
    z_score = (step_sizes - np.median(step_sizes)) / step_sizes.std()
    step_sizes = np.delete(step_sizes, np.abs(z_score) > 0.1)

    # calculate the average dll step size
    step_size = step_sizes.mean()
    unambiguity = calc_unambiguity_distance(modulation_freq_hz)
    return int(unambiguity / step_size)


def set_chip_temperature(cam: TOFcam, target_temp: float, max_deviation=MAX_ALLOWED_TEMP_DEVIATION) -> float:
    """Set the chip temperature of the camera to a target temperature by streaming images to heat up 
        or wait in idle until the camera to cools down

    Args:
        cam (TOFcam): TOFcam instance
        target_temp (float): Target temperature in degrees Celsius
        max_deviation (float, optional): Maximum allowed deviation from the target temperature before calibration starts

    Returns:
        float: The final temperature deviation
        """
    def get_temperature_diff(n_samples=10) -> float:
        temp = np.empty(n_samples)
        for i in range(n_samples):
            cam.get_grayscale_image()  # get a grayscale image to update the temperature
            temp[i] = cam.device.get_chip_temperature()
        return float(temp.mean()) - target_temp

    temp_diff = get_temperature_diff()  # max allowed std before calibration starts
    while np.abs(temp_diff) > max_deviation:  # max allowed deviation during calibration
        if temp_diff > 0:
            logger.info(
                f"cool down. Temperature difference: {temp_diff:04.3f} deg")
            time.sleep(15)
        else:
            logger.info(
                f"heat up. Temperature difference: {temp_diff:04.3f} deg")
            for i in range(50):
                cam.get_raw_dcs_images()
        temp_diff = get_temperature_diff()

    return temp_diff


def collect_calibration_data(cam: TOFcam, modulation_freq_hz: float, n_dll_steps: int, calib_temp: float, n_frames=50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Collect calibration data for the camera by capturing multiple frames at different DLL steps.
    This function captures a specified number of frames at each DLL step and calculates the distance and amplitude for each frame.

    Args:
        cam (TOFcam): TOFcam instance
        modulation_freq_hz (float): Modulation frequency in Hz
        n_dll_steps (int): Number of DLL steps to capture
        calib_temp (float): Target temperature for calibration in degrees Celsius
        n_frames (int, optional): Number of frames to capture at each DLL step. Defaults to 50.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: 
            - distances_mm: 4D array of shape (height, width, n_frames, n_dll_steps) containing distance images in mm
            - amplitudes_dn: 4D array of shape (height, width, n_frames, n_dll_steps) containing amplitude images in DN
            - temperatures_deg: 2D array of shape (n_frames, n_dll_steps) containing the chip temperature in degrees Celsius
    """
    x1, y1, x2, y2 = cam.settings.get_roi()
    resolution = (x2 - x1, y2 - y1)  # width, height
    distances_mm = np.empty(
        (resolution[1], resolution[0], n_frames, n_dll_steps))
    amplitudes_dn = np.empty(
        (resolution[1], resolution[0], n_frames, n_dll_steps))
    temperatures_deg = np.empty((n_frames, n_dll_steps))

    cam.settings.set_dll_step(0)
    for dll_step in range(n_dll_steps):
        cam.settings.set_dll_step(dll_step)
        set_chip_temperature(cam, calib_temp)
        for frame in np.arange(n_frames):
            print(
                f"Capturing frame {frame + 1}/{n_frames} at DLL step {dll_step + 1}/{n_dll_steps}...", end="\r")
            distance, amplitude = calc_distance_and_amplitude(
                cam.get_raw_dcs_images(), modulation_freq_hz)
            distances_mm[:, :, frame, dll_step] = distance
            amplitudes_dn[:, :, frame, dll_step] = amplitude
            cam.get_grayscale_image()  # get a grayscale image to update the temperature
            temperatures_deg[frame,
                             dll_step] = cam.device.get_chip_temperature()

    return distances_mm, amplitudes_dn, temperatures_deg


def calculate_offset_and_drnu_lut(distances: np.ndarray, modulation_freq_hz: float) -> Tuple[float, np.ndarray, np.ndarray]:
    """ This function calculates the offset and DRNU LUT from distance data collected with `collect_calibration_data()`

    Args:
        distances (np.ndarray): 4D array of shape (height, width, n_frames, n_dll_steps) containing distance images in mm
        modulation_freq_hz (float): Modulation frequency in Hz

    Returns:
        Tuple[float, np.ndarray]: 
            - offset: Average distance offset in mm
            - drnu_lut: 1D array of shape (n_dll_steps,) containing the DRNU LUT values in mm
            - dll_step_mm: The step size in mm for the DLL
    """
    # Do wrap around correction for the distances
    unambiguity_dist = calc_unambiguity_distance(modulation_freq_hz)
    step_sizes = np.diff(distances, axis=-1)  # insert 0 for the first step
    step_sizes = np.insert(step_sizes, 0, 0, axis=-1)
    mask_wrap_around = np.less(step_sizes, 0).cumsum(axis=-1).astype(bool)
    distance_corrected = distances + mask_wrap_around * unambiguity_dist

    # Calculate and correct average distance offset
    offset = np.mean(distance_corrected, axis=(0, 1, 2))[0]
    distance_corrected = distance_corrected - offset

    # Calculate DLL Step Size
    distances_dll = distance_corrected.mean(axis=(0, 1, 2))
    idx_closest_step_to_unambiguity = np.argmin(
        np.abs(distances_dll - unambiguity_dist))
    dist_closest_step_to_unambiguity = distances_dll[idx_closest_step_to_unambiguity]
    dll_step_mm = dist_closest_step_to_unambiguity / \
        (idx_closest_step_to_unambiguity)

    # Calculate DRNU LUT
    ref_distances = np.arange(0, dll_step_mm * len(distances_dll), dll_step_mm)
    drnu_lut = distance_corrected.mean(axis=2) - ref_distances

    return offset, drnu_lut, dll_step_mm
