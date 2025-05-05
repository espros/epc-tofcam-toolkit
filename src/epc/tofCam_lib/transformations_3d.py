import numpy as np
import importlib.resources

lens_type_map = {
    'Wide Field': importlib.resources.files('epc.data').joinpath('lense_calibration_wide_field.csv'),
    'Narrow Field':  importlib.resources.files('epc.data').joinpath('lense_calibration_narrow_field.csv'),
    'Standard Field':  importlib.resources.files('epc.data').joinpath('lense_calibration_standard_field.csv')
}

def get_camera_matrix(resolution, focalLength):

    # based on the pinhole camera model
    cx, cy = np.array(resolution) / 2.0
    fx = fy = focalLength
    camera_matrix = np.array([[fx, 0, cx],
                            [0, fy, cy],
                            [0, 0, 1]])
    return camera_matrix

def depth_to_3d(depth, resolution, focalLengh):

    camera_matrix = get_camera_matrix(resolution, focalLengh)
    # Get the shape of the depth image
    height, width = depth.shape

    # Create a grid of indices
    x, y = np.indices((height, width))

    # Normalize the x and y coordinates by the optical center
    x = (x - camera_matrix[0, 2]) / camera_matrix[0, 0]
    y = (y - camera_matrix[1, 2]) / camera_matrix[1, 1]

    # Stack the coordinates into a (3, N) array
    coords = np.stack((x, y, np.ones_like(x)), axis=0).reshape(3, -1)

    # Multiply the coordinates by the depth to get 3D points
    points = coords * depth.reshape(1, -1)
    points = points.reshape(3,height,width)

    return points


class Lense_Projection():

    def __init__(self, rp, angle, width=320, height=240, offsetX=0, offsetY=0):
        self.angle=np.zeros(101)
        self.rp=np.zeros(101)
        self.height=height
        self.width=width
        self.lenseMatrix = np.zeros((3, self.width, self.height))

        self.rp = rp
        self.angle = angle
        
        self.lensTableSize=100
        self.sensorPointSizeMM=0.02

        for y, row in enumerate(np.arange(-height/2, height/2)):
            row += 0.5
            for x, col in enumerate(np.arange(-width/2, width/2)):
                col += 0.5
                r = self.sensorPointSizeMM * np.sqrt(row**2 + col**2)
                
                # Find the closest rp and corresponding angle
                angle_deg = np.interp(r, rp, angle)
                angle_rad = np.deg2rad(angle_deg)
                rr = np.sqrt(row**2 + col**2)
                rUA = np.sin(angle_rad)

                self.lenseMatrix[0, x, y] = col * rUA / rr
                self.lenseMatrix[1, x, y] = row * rUA / rr
                self.lenseMatrix[2, x, y] = np.cos(angle_rad)

    @staticmethod
    def from_lense_calibration(lensType='Wide Field', width=320, height=240, offsetX=0, offsetY=0):
        file_path = lens_type_map.get(lensType)
        if file_path is None:
            raise KeyError(f"Invalid lensType '{lensType}'")
        angle, rp = np.loadtxt(file_path, delimiter=',', skiprows=1).T
        return Lense_Projection(rp, angle, width, height, offsetX, offsetY)

    def transformImage(self, depth: np.ndarray):
        return depth * self.lenseMatrix[:, 0:depth.shape[0], 0:depth.shape[1]]
    