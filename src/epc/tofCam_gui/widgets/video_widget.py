import numpy as np
from pyqtgraph import ImageView
from pyqtgraph.colormap import ColorMap, getFromMatplotlib
from pyqtgraph.opengl import (GLGridItem, GLLinePlotItem, GLScatterPlotItem,
                              GLViewWidget)
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from PySide6.QtGui import QQuaternion, QVector3D
from PySide6.QtWidgets import QStackedWidget

CMAP_DISTANCE = [(0,   0,   0),
                 (255,   0,   0),
                 (255, 255,   0),
                 (0, 255,   0),
                 (0, 240, 240),
                 (0,   0, 255),
                 (255,   0, 255)]

CMAP_GRAYSCALE = [(0, 0, 0),
                  (51, 51, 51),
                  (102, 102, 102),
                  (153, 153, 153),
                  (204, 204, 204),
                  (255, 255, 255)]


class Gizmo(GLGraphicsItem):
    def __init__(self, arrow_length=0.5, parent=None):
        super().__init__(parent)
        origin = np.array([0, 0, 0])
        x_axis = np.array([arrow_length, 0, 0])
        y_axis = np.array([0, arrow_length, 0])
        z_axis = np.array([0, 0, arrow_length])

        # Create the lines for the axes
        self.x_line = GLLinePlotItem(pos=np.array([origin, x_axis]), glOptions='opaque', color=(1, 0, 0, 1), width=6, antialias=True, parentItem=self)
        self.y_line = GLLinePlotItem(pos=np.array([origin, y_axis]), glOptions='opaque', color=(0, 1, 0, 1), width=6, antialias=True, parentItem=self)
        self.z_line = GLLinePlotItem(pos=np.array([origin, z_axis]), glOptions='opaque', color=(0, 0, 1, 1), width=6, antialias=True, parentItem=self)


class Camera(GLGraphicsItem):
    def __init__(self, offset=np.zeros(3), rotation=np.zeros(3), parent=None):
        super(Camera, self).__init__()
        self.offset = offset
        self.rotation = rotation
        self._gizmo = Gizmo(parent=self)
        self._pcd = GLScatterPlotItem(parentItem=self)
        self._pcd.initialize()
        self._pcd.setGLOptions('opaque')

    def update_position(self, offset=np.zeros(3), rotation=np.zeros(3)):
        self.offset = offset
        self.rotation = rotation
        self.resetTransform()
        self.rotate(rotation[0], 1, 0, 0)
        self.rotate(rotation[1], 0, 1, 0)
        self.rotate(rotation[2], 0, 0, 1)
        self.translate(*self.offset)

    def update_point_cloud(self, points: np.ndarray, amplitudes: np.ndarray):
        norm_amp = amplitudes / np.max(amplitudes)
        cmap = getFromMatplotlib('turbo')
        colors = cmap.map(norm_amp, 'float')

        self._pcd.setData(pos=points.T, color=colors, size=3)
        # print('latest step', points.shape)
        self.view().update()


class PointCloudWidget(GLViewWidget):
    def __init__(self, parent=None):
        super(PointCloudWidget, self).__init__(parent, rotationMethod='quaternion')
        self.camera = Camera(np.zeros(3), np.zeros(3))
        self.addItem(self.camera)
        self.grid = GLGridItem(size=QVector3D(10, 10, 1))
        self.grid.rotate(90, 1, 0, 0)
        self.grid.translate(0, -0.5, 0)
        self.addItem(self.grid)

        self.setCameraPosition(distance=4, pos=QVector3D(0, 1, 1), rotation=QQuaternion.fromEulerAngles(0, 180, 0))
        self.setMouseTracking(True)

    def update_point_cloud(self, points: np.ndarray):
        self.camera.update_point_cloud(points[0], points[1])


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
        data = args[0]
        if self.currentWidget() == self.video:
            self.video.setImage(*args, **kwargs)
        else:
            self.pc.update_point_cloud(data)

    def setColorMap(self, cmap):
        self.video.setColorMap(cmap)

    def setLevels(self, min, max):
        self.video.setLevels(min, max)
