import numpy as np
import cv2
from pyqtgraph import ImageView
from pyqtgraph.colormap import getFromMatplotlib, ColorMap
from pyqtgraph.opengl import GLViewWidget, GLScatterPlotItem, GLGridItem
from PySide6.QtGui import QQuaternion, QVector3D
from PySide6.QtWidgets import QStackedWidget
from epc.tofCam_lib.transformations_3d import depth_to_3d


CMAP_DISTANCE = [   (  0,   0,   0),
                    (255,   0,   0),
                    (255, 255,   0),
                    (  0, 255,   0),
                    (  0, 240, 240),
                    (  0,   0, 255),
                    (255,   0, 255)]

CMAP_GRAYSCALE =  [ (0, 0, 0),
                    (51, 51, 51),
                    (102, 102, 102),
                    (153, 153, 153),
                    (204, 204, 204),
                    (255, 255, 255)]

MXT = np.array([
            [117.65908368,   0.        , 154.48399236],
            [  0.        , 115.15310731, 126.99638559],
            [  0.        ,   0.        ,   1.        ]])

DIST = np.array([[ 6.31494575e-01, -3.06389796e+00, -1.31581191e-02, -6.54674525e-04,  3.29421024e+00]])


class PointCloudWidget(GLViewWidget):
    def __init__(self, parent=None):
        super(PointCloudWidget, self).__init__(parent, rotationMethod='quaternion')
        self.pcd = GLScatterPlotItem()
        self.addItem(self.pcd)
        grid = GLGridItem()
        grid.rotate(90, 1, 0, 0)
        grid.translate(0, -5, -2)
        self.addItem(grid)
        self.setMouseTracking(True)
        self.__maxDepth = 16000

    def set_max_depth(self, maxDepth: int):
        self.__maxDepth = maxDepth

    def set_pc_from_depth(self, depth: np.ndarray):
        depth[depth >= self.__maxDepth] = np.nan

        result = cv2.undistort(depth, MXT, DIST, None, None)
        points = depth_to_3d(result, MXT)

        norm_depths = points[2] / self.__maxDepth
        norm_depths[norm_depths > 1] = np.nan
        norm_depths = np.nan_to_num(norm_depths)

        cmap = getFromMatplotlib('turbo')

        colors = cmap.map(norm_depths, 'float')
        self.pcd.setData(pos=-0.01*points.T, color=colors, size=1)
        

class VideoWidget(QStackedWidget):
    GRAYSCALE_CMAP = ColorMap(pos=np.linspace(0.0, 1.0, 6), color=CMAP_GRAYSCALE)
    DISTANCE_CMAP = ColorMap(pos=np.linspace(0.0, 1.0, 6), color=CMAP_DISTANCE)
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.video = ImageView(self)
        self.pc = PointCloudWidget()
        self.addWidget(self.video)
        self.addWidget(self.pc)

    def setActiveView(self, view: str):
        if view == 'image':
            self.setCurrentWidget(self.video)
        elif view == 'pointcloud':
            self.setCurrentWidget(self.pc)

    def setImage(self, *args, **kwargs):
        if self.currentWidget() == self.video:
            self.video.setImage(*args, **kwargs)
        else:
            depth = args[0]
            depth = depth.astype(np.float32)
            self.pc.set_pc_from_depth(depth)
            

    def setPointCloud(self, points: np.ndarray):
        self.pc.update_ake(points)

    def setColorMap(self, cmap):
         self.video.setColorMap(cmap)

    def setLevels(self, min, max):
        self.video.setLevels(min, max)