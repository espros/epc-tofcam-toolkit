import numpy as np
from typing import Tuple

C = 299792458  # m/s

def calc_amplitude(cx: np.ndarray, cy: np.ndarray) -> np.ndarray:
    """calculate the amplitude for two orthagonal dcs images

    :param cx: dcs image in x direction
    :param cy: dcs image in y direction
    """

    squared_sum = cx.astype(float)**2 + cy.astype(float)**2
    amplitude = np.sqrt(squared_sum) / 2
    return np.array(amplitude, dtype=np.float32) 

def diff_dcs(dcs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate the difference of two opposite dcs images and return as cx, cy pair.
    """
    if dcs.shape[0] != 4:
        raise ValueError('dcs must have shape (4, height, width)')

    cx = dcs[0] - dcs[2]
    cy = dcs[1] - dcs[3]

    return cx, cy

def calc_distance(cx: np.ndarray, cy: np.ndarray, modFreq_hz: float) -> np.ndarray:
    """Calculate the distance image from the cx, cy pair and the modulation frequency.

    :param cx: dcs image in x direction
    :param cy: dcs image in y direction
    :param modFreq_hz: modulation frequency in Hz
    :return: distance image in mm
    """
    phi = np.arctan2(cy, cx)
    return 1E3 * np.array(phi) * C / (4*np.pi*modFreq_hz)  # distance in mm

def calc_unambiguity_distance(modFreq_hz: float) -> float:
    """Calculate the unambiguity distance for a given modulation frequency.

    :param modFreq_hz: modulation frequency in Hz
    :return: unambiguity distance in mm
    """
    return C / (2 * modFreq_hz) * 1E3  # unambiguity distance in mm

def calc_distance_and_amplitude(dcs: np.ndarray, modFreq_hz: float) -> tuple[np.ndarray, np.ndarray]:
    """Calculate the distance and amplitude from a dcs images.

    Args:
        dcs (np.ndarray): _description_
        modFreq_hz (float): _description_

    Returns:
        tuple[np.ndarray, np.ndarray]: _description_
    """
    cx, cy = diff_dcs(dcs)

    amp = calc_amplitude(cx, cy)
    dist = calc_distance(cx, cy, modFreq_hz)
    return (dist, amp)