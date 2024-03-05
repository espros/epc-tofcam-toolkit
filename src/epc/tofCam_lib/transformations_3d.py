import numpy as np
import math

def depth_to_3d(depth, camera_matrix):
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

    return points


class Lense_Projection():

    def __init__(self,rp, angle, width=320,height=240,offsetX=0,offsetY=0):
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


    def from_lense_calibration(offset=(0,0), 
                               file_path: str = 'src/epc/data/lense_calibration.csv'):
        angle, rp = np.loadtxt(file_path, delimiter=',', skiprows=1).T
        return Lense_Projection(rp, angle)

    def transformImage(self, depth: np.array, roi=None):
        if roi is not None:
            return depth * self.lenseMatrix[:, roi[0]:roi[1], roi[2]:roi[3]]
        return depth * self.lenseMatrix
    



if __name__ == '__main__':
    Lense_Projection.from_lense_calibration()
    proj = Lense_Projection.from_lense_calibration(0.02, (320, 240))
    res = proj.depth_to_3d(np.ones((320, 240)))
    print(res)