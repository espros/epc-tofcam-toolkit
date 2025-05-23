from typing import Optional

import numpy as np
from epc.tofCam_gui.icon_svg import SVG_DICT, svg2icon
from pyqtgraph import ImageView, TextItem
from pyqtgraph.colormap import ColorMap, getFromMatplotlib
from pyqtgraph.opengl import (GLGridItem, GLLinePlotItem, GLScatterPlotItem,
                              GLViewWidget)
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QQuaternion, QVector3D
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                               QStackedWidget, QVBoxLayout, QWidget)

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
        self.x_line = GLLinePlotItem(pos=np.array([origin, x_axis]), glOptions='opaque', color=(
            1, 0, 0, 1), width=6, antialias=True, parentItem=self)
        self.y_line = GLLinePlotItem(pos=np.array([origin, y_axis]), glOptions='opaque', color=(
            0, 1, 0, 1), width=6, antialias=True, parentItem=self)
        self.z_line = GLLinePlotItem(pos=np.array([origin, z_axis]), glOptions='opaque', color=(
            0, 0, 1, 1), width=6, antialias=True, parentItem=self)


class Camera(GLGraphicsItem):
    def __init__(self, offset=np.zeros(3), rotation=np.zeros(3), parent=None):
        super(Camera, self).__init__()
        self.offset = offset
        self.rotation = rotation
        self._gizmo = Gizmo(parent=self)
        self._pcd = GLScatterPlotItem(parentItem=self, glOptions='opaque')
        QTimer.singleShot(0, self.safe_init)

    def safe_init(self) -> None:
        """Delay the initialization until the OpenGL context is ready"""
        if hasattr(self._pcd, "initialize"):
            self._pcd.initialize()

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
        super(PointCloudWidget, self).__init__(
            parent, rotationMethod='quaternion')
        self.camera = Camera(np.zeros(3), np.zeros(3))
        self.addItem(self.camera)
        self.grid = GLGridItem(size=QVector3D(10, 10, 1))
        self.grid.rotate(90, 1, 0, 0)
        self.grid.translate(0, -0.5, 0)
        self.addItem(self.grid)

        self.setCameraPosition(distance=4, pos=QVector3D(
            0, 1, 1), rotation=QQuaternion.fromEulerAngles(0, 180, 0))
        self.setMouseTracking(True)

    def update_point_cloud(self, points: np.ndarray):
        self.camera.update_point_cloud(points[0], points[1])


class VideoSlider(QWidget):
    frame_idx_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):

        super().__init__(parent=parent)
        self.setVisible(False)
        self.slider = QSlider(Qt.Orientation.Horizontal, parent=parent)
        self.playButton = QPushButton(self)
        self.playButton.setIcon(svg2icon(SVG_DICT["play"]))
        self.playButton.setCheckable(True)
        self.playButton.toggled.connect(self._playButtonToggled)

        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #ccc;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #aaa;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #FF0000;
            }
        """)
        self.index = 0
        self.total = 0

        self.label = QLabel(f"{self.index} / {self.total}")

        _layout = QHBoxLayout(self)
        _layout.addWidget(self.playButton)
        _layout.addWidget(self.slider)
        _layout.addWidget(self.label)
        self.setLayout(_layout)
        self.setEnabled(False)

        self.slider.valueChanged.connect(self.on_value_changed)

    def _playButtonToggled(self) -> None:
        self.__setOnOffIcons(
            self.playButton, svg2icon(SVG_DICT["play"]), svg2icon(SVG_DICT["pause"]))

    def __setOnOffIcons(self, button: QPushButton, on: QIcon, off: QIcon) -> None:
        """Set ON/OFF icon variations for the same button

        Args:
            button (QAction): The button to set the icons
            on (QIcon): ON icon
            off (QIcon): OFF icon
        """
        if button.isChecked():
            button.setIcon(off)
        else:
            button.setIcon(on)

    def update_record(self, total: int) -> None:
        """Update the slider label"""
        self.slider.setRange(0, total)
        self.slider.setValue(0)
        self.update_label(index=0, total=total)
        self.setEnabled(True)

    def update_label(self, index: Optional[int] = None, total: Optional[int] = None) -> None:
        if index is not None:
            self.index = index
        if total is not None:
            self.total = total
        self.label.setText(f"{self.index} / {self.total}")

    def on_value_changed(self, value: int) -> None:
        """Update the label and emit frame index changed"""
        self.index = value
        self.label.setText(f"{self.index} / {self.total}")
        self.frame_idx_changed.emit(value)


class VideoWidget(QWidget):
    GRAYSCALE_CMAP = ColorMap(pos=np.linspace(
        0.0, 1.0, 6), color=CMAP_GRAYSCALE)
    DISTANCE_CMAP = getFromMatplotlib('turbo')

    def __init__(self, parent=None):
        self._updating_label = False
        super(VideoWidget, self).__init__(parent)
        self.video = ImageView(self)
        self.pc = PointCloudWidget(self)
        self.slider = VideoSlider(parent=self)

        # Handle source label
        self.source_label = TextItem("epc", color="y", anchor=(0, 1))

        # Stack
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.video)
        self.stacked.addWidget(self.pc)

        # Layout
        _layout = QVBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.addWidget(self.stacked)
        _layout.addWidget(self.slider)
        self.setLayout(_layout)

        # Update text position
        self.video.getView().sigResized.connect(self.update_source_label_position_image)

    def update_source_label_position_image(self):
        """Kepp the label at the bottom left"""
        view = self.video.getView()
        rect = view.sceneBoundingRect()
        margin = 10
        x = rect.left() + margin
        y = rect.bottom() - margin
        self.source_label.setPos(x, y)

    def setActiveView(self, view: str):
        if view == 'image':
            self.stacked.setCurrentWidget(self.video)
        elif view == 'pointcloud':
            self.stacked.setCurrentWidget(self.pc)

    def setImage(self, *args, **kwargs):
        data = args[0]
        if self.stacked.currentWidget() == self.video:
            self.video.setImage(*args, **kwargs)
            if self.source_label.scene() is None:
                self.video.scene.addItem(self.source_label)
                self.update_source_label_position_image()
        else:
            self.pc.update_point_cloud(data)

    def setColorMap(self, cmap):
        self.video.setColorMap(cmap)

    def setLevels(self, min, max):
        self.video.setLevels(min, max)
