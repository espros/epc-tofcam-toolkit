import numpy as np

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