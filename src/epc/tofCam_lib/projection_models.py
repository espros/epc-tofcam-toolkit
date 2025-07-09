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

DEFAULT_PIXEL_SIZE_MM = 0.0


class PinholeCameraProjector:
    def __init__(self, resolution: Tuple[int, int], focal_length_mm: float, pixel_size_mm=DEFAULT_PIXEL_SIZE_MM):
        """
        Initialize the PinholeCameraProjector with resolution, focal length, and pixel size.
        Args:
            resolution (Tuple[int, int]): Resolution of the camera in pixels (height, width).
            focal_length_mm (float): Focal length of the camera in millimeters.
            pixel_size_mm (float): Size of a pixel in millimeters.
        """

        self.focal_length_mm = focal_length_mm
        self.pixel_size_mm = pixel_size_mm

        # Create a grid of indices
        self.height, self.width = resolution
        y, x = np.indices((self.height, self.width))
        x = x - self.width/2 + 0.5
        y = y - self.height/2 + 0.5
        x *= self.pixel_size_mm
        y *= self.pixel_size_mm

        # Precalculate Lens Matrix
        dir_matrix = np.stack(
            (x, -y, np.ones_like(x) * focal_length_mm), axis=0).reshape(3, -1)
        self._lens_matrix: np.ndarray = dir_matrix / \
            np.linalg.norm(dir_matrix, axis=0)
        self._lens_matrix = self._lens_matrix.reshape(
            3, self.height, self.width)

    def project(self, depth: np.ndarray, roi_x=0, roi_y=0) -> np.ndarray:
        """ Project a depth image to 3D points using the pinhole camera model.

        Args:
            depth (np.ndarray): Depth image to be projected, should match the dimensions of the lens matrix.
            roi_x (int, optional): Region of interest x-coordinate.
            roi_y (int, optional): Region of interest y-coordinate.

        Returns:
            np.ndarray: Projected 3D points in the format (3, height, width).
        """
        roi_height, roi_width = depth.shape
        assert roi_x >= 0 and roi_y >= 0 and \
            roi_x + roi_width <= self.width and roi_y + roi_height <= self.height, \
            "ROI exceeds image dimensions"
        points: np.ndarray = self._lens_matrix[:, roi_y:roi_y + roi_height,
                                               roi_x:roi_x+roi_width] * depth
        return points


class RadialCameraProjector:
    def __init__(self, rp: np.ndarray, angle: np.ndarray, width: int, height: int, pixel_size_mm=DEFAULT_PIXEL_SIZE_MM):
        """ Initialize the RadialCameraProjector with radial parameters and image dimensions.

        Args:
            rp (np.ndarray): array of radial distances in mm
            angle (np.ndarray): array of angles in degrees corresponding to the radial distances
            width (int): _width of the image in pixels_
            height (int): _height of the image in pixels_
        """
        self.angle = np.array(angle)
        self.rp = np.array(rp)
        self.height = height
        self.width = width
        self.lens_matrix: np.ndarray = np.zeros((3, self.height, self.width))

        # Create coordinate grids
        y_idx, x_idx = np.indices((height, width))
        row = x_idx - width / 2 + 0.5
        col = y_idx - height / 2 + 0.5
        col *= -1  # Invert y-axis for camera coordinates

        rr = np.sqrt(row**2 + col**2)
        r = pixel_size_mm * rr

        # Interpolate angle for each radius
        angle_deg = np.interp(r, self.rp, self.angle)
        angle_rad = np.deg2rad(angle_deg)
        rUA = np.sin(angle_rad)

        # Avoid division by zero
        rr_safe = np.where(rr == 0, 1, rr)

        self.lens_matrix[0] = row * rUA / rr_safe
        self.lens_matrix[1] = col * rUA / rr_safe
        self.lens_matrix[2] = np.cos(angle_rad)

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
        roi_height, roi_width = depth.shape
        assert roi_x >= 0 and roi_y >= 0 and \
            roi_x + roi_width <= self.width and roi_y + roi_height <= self.height, \
            "ROI exceeds image dimensions"
        points: np.ndarray = self.lens_matrix[:, roi_y:roi_y + roi_height,
                                              roi_x:roi_x+roi_width] * depth
        return points
