import numpy as np
from typing import Tuple

DEFAULT_PIXEL_SIZE_MM = 0.02


class LinearXYZTransformation:
    def __init__(self, resolution: Tuple[int, int], focal_lenght_mm: float, pixel_size_mm=DEFAULT_PIXEL_SIZE_MM):
        self.focal_length_mm = focal_lenght_mm
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
        self._lens_matrix = np.stack(
            (x, y, np.ones_like(x) * focal_lenght_mm), axis=0).reshape(3, -1)
        self._lens_matrix = self._lens_matrix / \
            np.linalg.norm(self._lens_matrix, axis=0)

    def transform(self, depth_image: np.ndarray):
        assert depth_image.shape == self._resolution, "distance image has to be of same resolution as the lens matrix"
        points = self._lens_matrix * depth_image.reshape(1, -1)
        return points
