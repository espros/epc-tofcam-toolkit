import numpy as np
from typing import Tuple
import importlib.resources

lens_type_map = {
    'Wide Field': importlib.resources.files('epc.data').joinpath('lense_calibration_wide_field.csv'),
    'Narrow Field':  importlib.resources.files('epc.data').joinpath('lense_calibration_narrow_field.csv'),
    'Standard Field':  importlib.resources.files('epc.data').joinpath('lense_calibration_standard_field.csv')
}

DEFAULT_PIXEL_SIZE_MM = 0.02


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
        self._resolution = resolution

        # Create a grid of indices
        height, width = resolution
        x, y = np.indices((height, width))
        x = x - height/2 + 0.5
        y = y - width/2 + 0.5
        x *= self.pixel_size_mm
        y *= self.pixel_size_mm

        # Precalculate Lens Matrix
        dir_matrix = np.stack(
            (x, y, np.ones_like(x) * focal_length_mm), axis=0).reshape(3, -1)
        self._lens_matrix: np.ndarray = dir_matrix / \
            np.linalg.norm(dir_matrix, axis=0)
        self._lens_matrix = self._lens_matrix.reshape(3, height, width)

    def project(self, depth_image: np.ndarray) -> np.ndarray:
        """ Project a depth image to 3D points using the pinhole camera model.

        Args:
            depth_image (np.ndarray): Depth image to be projected, should match the dimensions of the lens matrix.

        Returns:
            np.ndarray: Projected 3D points in the format (3, height, width).
        """
        assert depth_image.shape == self._resolution, "distance image has to be of same resolution as the lens matrix"
        points: np.ndarray = self._lens_matrix * depth_image
        return points


class RadialCameraProjector:
    def __init__(self, rp: np.ndarray, angle: np.ndarray, width: int, height: int):
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
        self.lens_matrix: np.ndarray = np.zeros((3, self.width, self.height))

        self.lensTableSize = 100
        self.sensorPointSizeMM = 0.02

        # Create coordinate grids
        y_idx, x_idx = np.indices((width, height))
        row = y_idx - width / 2 + 0.5
        col = x_idx - height / 2 + 0.5

        rr = np.sqrt(row**2 + col**2)
        r = self.sensorPointSizeMM * rr

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

    def project(self, depth: np.ndarray) -> np.ndarray:
        """ Project a depth image to 3D points using the radial camera model.
        Args:
            depth (np.ndarray): Depth image to be projected, should match the dimensions of the lens matrix.
        Returns:
            np.ndarray: Projected 3D points in the format (3, width, height).
        """
        assert depth.shape == (
            self.width, self.height), "Only full image Projections are supported"
        points: np.ndarray = self.lens_matrix * depth
        return points
