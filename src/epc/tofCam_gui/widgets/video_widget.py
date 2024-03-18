import numpy as np
from pyqtgraph import ImageView
from pyqtgraph.colormap import getFromMatplotlib, ColorMap
from pyqtgraph.opengl import GLViewWidget, GLScatterPlotItem, GLGridItem
from PySide6.QtGui import QVector3D, QQuaternion
from PySide6.QtWidgets import QStackedWidget

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


class PointCloudWidget(GLViewWidget):
    def __init__(self, parent=None):
        super(PointCloudWidget, self).__init__(parent, rotationMethod='quaternion')
        self.pcd = GLScatterPlotItem()
        self.pcd.setGLOptions('translucent')
        self.addItem(self.pcd)
        grid = GLGridItem(size=QVector3D(10, 10, 1))
        grid.rotate(90, 1, 0, 0)
        grid.translate(0, -0.5, 0)
        self.setCameraPosition(distance=4, pos=QVector3D(0, 0.3, 3), rotation=QQuaternion.fromEulerAngles(180, 0, 180))
        self.addItem(grid)
        self.setMouseTracking(True)
        self.__maxDepth = 6.25 # unambiguity distance in m

    def set_max_depth(self, maxDepth: int):
        self.__maxDepth = maxDepth

    def set_pc_from_depth(self, points: np.ndarray):
        dists = np.linalg.norm(points, axis=1)
        norm_depths = dists / self.__maxDepth
        norm_depths[norm_depths > 1] = np.nan
        norm_depths = np.nan_to_num(norm_depths)
        cmap = getFromMatplotlib('turbo')
        colors = cmap.map(norm_depths, 'float')
        self.pcd.setData(pos=np.nan_to_num(points), color=colors, size=3)
        

class VideoWidget(QStackedWidget):
    GRAYSCALE_CMAP = ColorMap(pos=np.linspace(0.0, 1.0, 6), color=CMAP_GRAYSCALE)
    DISTANCE_CMAP = getFromMatplotlib('turbo')
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
            self.pc.set_pc_from_depth(depth)

    def setColorMap(self, cmap):
         self.video.setColorMap(cmap)

    def setLevels(self, min, max):
        self.video.setLevels(min, max)