import numpy as np
from typing import Tuple
import importlib.resources
import logging

logger = logging.getLogger(__name__)

lens_type_map = {
    'Wide Field': importlib.resources.files('epc.data').joinpath('lense_calibration_wide_field.csv'),
    'Narrow Field':  importlib.resources.files('epc.data').joinpath('lense_calibration_narrow_field.csv'),
    'Standard Field':  importlib.resources.files('epc.data').joinpath('lense_calibration_standard_field.csv')
}

DEFAULT_PIXEL_SIZE_MM = 0.02


def _project_points(lens_matrix: np.ndarray, depth: np.ndarray, roi_x=0, roi_y=0) -> np.ndarray:
    """ Project a depth image to 3D points using the radial camera model.
    Args:
        lens_matrix (np.ndarray): Lens matrix containing the camera model parameters.
        depth (np.ndarray): Depth image to be projected, should match the dimensions of the lens matrix.
        width (int): Width of the image in pixels.
        height (int): Height of the image in pixels.
        roi_x (int, optional): Region of interest x-coordinate.
        roi_y (int, optional): Region of interest y-coordinate.
    Returns:
        np.ndarray: Projected 3D points
    """
    roi_height, roi_width = depth.shape
    height, width = lens_matrix.shape[1:3]
    assert roi_x >= 0 and roi_y >= 0 and \
        roi_x + roi_width <= width and roi_y + roi_height <= height, \
        "ROI exceeds image dimensions"
    points: np.ndarray = lens_matrix[:, roi_y:roi_y + roi_height,
                                     roi_x:roi_x+roi_width] * depth
    return points


def _create_pixel_field_indices(height: int, width: int, pixel_size_mm: float) -> Tuple[np.ndarray, np.ndarray]:
    """ Create pixel field indices for the camera projection.

    Args:
        height (int): Height of the image in pixels.
        width (int): Width of the image in pixels.
        pixel_size_mm (float): Size of a pixel in millimeters.

    Returns:
        Tuple[np.ndarray, np.ndarray]: x and y indices for the pixel field.
    """
    y, x = np.indices((height, width))
    x = x - width / 2 + 0.5
    y = y - height / 2 + 0.5
    x *= pixel_size_mm
    y *= pixel_size_mm
    return x, -y


class PinholeCameraProjector:
    def __init__(self, resolution: Tuple[int, int], focal_length_mm: float, pixel_size_mm=DEFAULT_PIXEL_SIZE_MM):
        """
        Initialize the PinholeCameraProjector with resolution, focal length, and pixel size.
        Args:
            resolution (Tuple[int, int]): Resolution of the camera in pixels (height, width).
            focal_length_mm (float): Focal length of the camera in millimeters.
            pixel_size_mm (float): Size of a pixel in millimeters.
        """
        # Create a grid of indices
        height, width = resolution
        x, y = _create_pixel_field_indices(height, width, pixel_size_mm)

        # Precalculate Lens Matrix
        dir_matrix = np.stack(
            (x, y, np.ones_like(x) * focal_length_mm), axis=0)
        self._lens_matrix: np.ndarray = dir_matrix / \
            np.linalg.norm(dir_matrix, axis=0)

    def project(self, depth: np.ndarray, roi_x=0, roi_y=0) -> np.ndarray:
        """ Project a depth image to 3D points using the pinhole camera model.

        Args:
            depth (np.ndarray): Depth image to be projected, should match the dimensions of the lens matrix.
            roi_x (int, optional): Region of interest x-coordinate.
            roi_y (int, optional): Region of interest y-coordinate.

        Returns:
            np.ndarray: Projected 3D points in the format (3, height, width).
        """
        return _project_points(self._lens_matrix, depth, roi_x, roi_y)


class RadialCameraProjector:
    def __init__(self, rp: np.ndarray, angle: np.ndarray, width: int, height: int, pixel_size_mm=DEFAULT_PIXEL_SIZE_MM):
        """ Initialize the RadialCameraProjector with radial parameters and image dimensions.

        Args:
            rp (np.ndarray): array of radial distances in mm
            angle (np.ndarray): array of angles in degrees corresponding to the radial distances
            width (int): _width of the image in pixels_
            height (int): _height of the image in pixels_
        """
        row, col = _create_pixel_field_indices(
            height, width, pixel_size_mm
        )

        radius = np.sqrt(row**2 + col**2)

        # Interpolate angle for each radius
        angle_deg = np.interp(radius, rp, angle)
        angle_rad = np.deg2rad(angle_deg)
        rUA = np.sin(angle_rad)

        # Avoid division by zero
        rr_safe = np.where(radius == 0, 1, radius)

        self._lens_matrix: np.ndarray = np.zeros((3, height, width))
        self._lens_matrix[0] = row * rUA / rr_safe
        self._lens_matrix[1] = col * rUA / rr_safe
        self._lens_matrix[2] = np.cos(angle_rad)

    @staticmethod
    def from_lens_calibration(lensType: str, width: int, height: int) -> 'RadialCameraProjector':
        """ Create a RadialCameraProjector from a known lens type.

        Args:
            lensType (str): _Description of the lens type, e.g., 'Wide Field', 'Narrow Field', 'Standard Field'_
            width (int): _width of the image in pixels_
            height (int): _height of the image in pixels_

        Returns:
            RadialCameraProjector: An instance of RadialCameraProjector initialized with the lens calibration data.
        """
        file_path = lens_type_map.get(lensType)
        if file_path is None:
            raise KeyError(f"Invalid lensType '{lensType}'")
        angle, rp = np.loadtxt(str(file_path), delimiter=',', skiprows=1).T
        return RadialCameraProjector(rp, angle, width, height)

    @staticmethod
    def from_radial_coefficients(coeffs: np.ndarray, width: int, height: int, pixel_size_mm=DEFAULT_PIXEL_SIZE_MM):
        """ Create a RadialCameraProjector from radial coefficients.

        Args:
            coeffs (np.ndarray): Coefficients of the polynomial defining the radial distortion.
            width (int): Width of the image in pixels.
            height (int): Height of the image in pixels.
            pixel_size_mm (float): Size of a pixel in millimeters
        """
        max_radius = (width/2) * (height/2) * pixel_size_mm
        r = np.linspace(0, max_radius, 2000)
        angle = np.polyval(coeffs, r)
        return RadialCameraProjector(r, angle, width, height)

    def project(self, depth: np.ndarray, roi_x=0, roi_y=0) -> np.ndarray:
        """ Project a depth image to 3D points using the radial camera model.
        Args:
            depth (np.ndarray): Depth image to be projected
            roi_x (int, optional): Region of interest x-coordinate.
            roi_y (int, optional): Region of interest y-coordinate.
        Returns:
            np.ndarray: Projected 3D points in the format (3, width, height).
        """
        return _project_points(self._lens_matrix, depth, roi_x, roi_y)
