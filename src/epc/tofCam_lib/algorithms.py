from typing import Tuple

import numpy as np

C = 299792458  # m/s


def calc_amplitude(cx: np.ndarray, cy: np.ndarray) -> np.ndarray:
    """Calculate the amplitude for two orthagonal dcs images

    Args:
        cx (np.ndarray): dcs image in x direction
        cy (np.ndarray): dcs image in y direction

    Returns:
        np.ndarray: calculated amplitude
    """

    squared_sum = cx.astype(float)**2 + cy.astype(float)**2
    amplitude = np.sqrt(squared_sum) / 2
    return np.array(amplitude, dtype=np.float32)


def diff_dcs(dcs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate the difference of two opposite dcs images and return as cx, cy pair.

    Args:
        dcs (np.ndarray): 4 dcs frames stacked together (4, height, width)

    Returns:
        Tuple[np.ndarray, np.ndarray]: cx, cy pair
            cx: dcs image in x direction, 
            cy: dcs image in y direction
    """
    if dcs.shape[0] != 4:
        raise ValueError('dcs must have shape (4, height, width)')

    cx = dcs[2] - dcs[0]
    cy = dcs[3] - dcs[1]

    return cx, cy


def calc_phase(cx: np.ndarray, cy: np.ndarray) -> np.ndarray:
    """Calculate the phase from cx, cy pair

    Args:
        cx (np.ndarray): dcs image in x direction
        cy (np.ndarray): dcs image in y direction

    Returns:
        np.ndarray: phase image
    """
    return np.array(np.arctan2(cy, cx))


def calc_dist_from_phase(phase: np.ndarray, mod_freq_hz: float) -> np.ndarray:
    """Calculate the distance image from the phase image and the modulation frequency

    Args:
        phase (np.ndarray): phase image
        mod_freq_hz (float): modulation frequency in Hz
    Returns:
        np.ndarray: distance image in mm
    """
    return 1E3 * (phase + np.pi) * C / (4*np.pi*mod_freq_hz)  # distance in mm


def calc_distance(cx: np.ndarray, cy: np.ndarray, mod_freq_hz: float) -> np.ndarray:
    """Calculate the distance image from the cx, cy pair and the modulation frequency

    Args:
        cx (np.ndarray): dcs image in x direction
        cy (np.ndarray): dcs image in y direction
        mod_freq_hz (float): modulation frequency in Hz

    Returns:
        np.ndarray: distance image in mm
    """
    phi = calc_phase(cx, cy)  # shift phase to [0, 2*pi]
    return calc_dist_from_phase(phi, mod_freq_hz)


def calc_unambiguity_distance(mod_freq_hz: float) -> float:
    """Calculate the unambiguity distance for a given modulation frequency

    Args:
        mod_freq_hz (float): modulation frequency in Hz

    Returns:
        float: unambiguity distance in mm
    """
    return C / (2 * mod_freq_hz) * 1E3  # unambiguity distance in mm


def calc_distance_and_amplitude(dcs: np.ndarray, mod_freq_hz: float) -> tuple[np.ndarray, np.ndarray]:
    """Calculate the distance and amplitude from a dcs images.

    Args:
        dcs (np.ndarray): 4 dcs frames stacked together (4, height, width)
        mod_freq_hz (float): modulation frequency in Hz

    Returns:
        tuple[np.ndarray, np.ndarray]: dist, amp
            dist: distance array
            amp: amplitude array
    """
    cx, cy = diff_dcs(dcs)

    amp = calc_amplitude(cx, cy)
    dist = calc_distance(cx, cy, mod_freq_hz)
    return (dist, amp)
