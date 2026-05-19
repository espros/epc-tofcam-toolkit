from typing import Optional

import numpy as np
from epc.tofCam_gui.icon_svg import svg2icon
from epc.tofCam_lib.h5Cam import H5Cam
from pyqtgraph import ImageView, HistogramLUTWidget
from pyqtgraph.colormap import ColorMap, getFromMatplotlib
from pyqtgraph.opengl import (GLGridItem, GLLinePlotItem, GLScatterPlotItem,
                              GLViewWidget)
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QQuaternion, QVector3D
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider, QComboBox,
                               QStackedWidget, QToolTip, QVBoxLayout, QWidget)

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

MAX_AMPLITUDE = 2894

class Gizmo(GLGraphicsItem):
    def __init__(self, arrow_length=0.5, parent=None):
        super().__init__(parent)
        origin = np.array([0, 0, 0])
        x_axis = np.array([-arrow_length, 0, 0]) # Flip x-axis for OpenGL
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
        self._color_map = 'amplitude'

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

    def set_color_map(self, color_map = 'amplitude'):
        if color_map not in ['distance', 'amplitude']:
            raise ValueError(f"Unsupported color map: {color_map}")
        self._color_map = color_map

    def update_point_cloud(self, points: np.ndarray, colors):
        points = np.astype(points, np.float64)
        points[0] *= -1  # Flip x axis since OpenGL uses right-handed coordinate system
        self._pcd.setData(pos=points.T, color=colors, size=3)
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

        self.histogram = HistogramLUTWidget(self)
        self.histogram.setFixedWidth(150)
        self.histogram.item.sigLookupTableChanged.connect(self._color_map_changed)

        self.reset_btn = QPushButton("Reset View", self)
        self.reset_btn.resize(100, 30)
        self.reset_btn.clicked.connect(self.reset_view)
        self.reset_btn.setToolTip("Reset the camera view to default position")

        self.color_map_selector = QComboBox(self)
        self.color_map_selector.addItems(["Distance", "Amplitude"])
        self.color_map_selector.setCurrentIndex(0)
        self.color_map_selector.setToolTip("Select color map for point cloud")
        self.color_map_selector.currentTextChanged.connect(self.setColorMap)
        self.color_map_selector.currentTextChanged.emit(self.color_map_selector.currentText())

        self.histogram.item.gradient.setColorMap(VideoWidget.AMPLITUDE_CMAP)
        self.reset_view()
        self.setMouseTracking(True)

    def _color_map_changed(self, text):
        self._cmap = self.histogram.item.gradient.colorMap()

    def setColorMap(self, cmap):
        if cmap == 'Distance':
            self._cmap = VideoWidget.DISTANCE_CMAP
        elif cmap == 'Amplitude':
            self._cmap = VideoWidget.AMPLITUDE_CMAP
            self.histogram.setLevels(0, MAX_AMPLITUDE)
            self.histogram.item.setHistogramRange(0, MAX_AMPLITUDE)
        self.histogram.item.gradient.setColorMap(self._cmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = 10
        self.reset_btn.move(margin, self.height() - self.reset_btn.height() - margin)
        
        hist_w = self.histogram.width()
        self.histogram.setFixedHeight(self.height())
        self.histogram.move(self.width() - hist_w, 0)

        self.color_map_selector.move(self.width() - hist_w - self.color_map_selector.width() - margin, margin)
    
    def _get_scalar_values(self, points3d: np.ndarray, amplitudes: np.ndarray) -> np.ndarray:
        """Return the scalar values used for histogram and coloring based on the selected mode."""
        if self.color_map_selector.currentText() == 'Distance':
            return np.linalg.norm(points3d * 1000, axis=0)
        return amplitudes

    def update_point_cloud(self, points: np.ndarray, autolevels=False):
        points3d = points[0].copy().astype(float)
        amplitudes = points[1].copy().astype(float)

        scalars = self._get_scalar_values(points3d, amplitudes)
        finite_mask = np.isfinite(scalars)

        hist_range = (0, MAX_AMPLITUDE) if self.color_map_selector.currentText() == 'Amplitude' else None
        y, x = np.histogram(scalars[finite_mask], bins=256, range=hist_range)
        self.histogram.item.plot.setData(x, y, stepMode='center')

        if autolevels and finite_mask.any():
            self.histogram.item.region.setRegion([scalars[finite_mask].min(),
                                                  scalars[finite_mask].max()])

        roi_min, roi_max = self.histogram.item.region.getRegion()
        roi_mask = finite_mask & (scalars >= roi_min) & (scalars <= roi_max)

        points3d[:, ~roi_mask] = np.nan
        norm = np.where(roi_mask, (scalars - roi_min) / max(roi_max - roi_min, 1e-9), np.nan)
        colors = self._cmap.map(np.clip(norm, 0.0, 1.0), 'float')

        self.camera.update_point_cloud(points3d, colors)

    def reset_view(self):
        self.setCameraPosition(distance=4, pos=QVector3D(
            0, 1, 1), rotation=QQuaternion.fromEulerAngles(0, 180, 0))


class VideoSlider(QWidget):
    user_updated_slider = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None, cam: Optional[H5Cam] = None):

        self._icons = {_name: svg2icon(f"{_name}.svg")
                       for _name in ["play", "pause"]}

        super().__init__(parent=parent)
        self.setVisible(False)
        self.slider = QSlider(Qt.Orientation.Horizontal, parent=parent)
        self.slider.setMouseTracking(True)
        self.slider.installEventFilter(self)
        self.playButton = QPushButton(self)
        self.playButton.setIcon(self._icons["play"])
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

        self.label = QLabel(f"00:00.000 / 00:00.000")

        _layout = QHBoxLayout(self)
        _layout.addWidget(self.playButton)
        _layout.addWidget(self.slider)
        _layout.addWidget(self.label)
        self.setLayout(_layout)
        self.setEnabled(False)

        self._user_interaction = False
        self._slider_pressed = False
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)

        self.cam = None
        if cam is not None:
            self.update_cam(cam)

    def eventFilter(self, obj: QObject, event: QEvent):
        """Add a tooltip and index update action flag"""
        if event.type() == QEvent.Type.MouseMove:
            if self.cam is not None:
                QToolTip.showText(event.globalPosition().toPoint(
                ), f"{self.cam.index}/{len(self.cam)-1}")
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress):
            self._user_interaction = True
        return super().eventFilter(obj, event)

    def _playButtonToggled(self) -> None:
        self.__setOnOffIcons(
            self.playButton, self._icons["play"], self._icons["pause"])

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

    def update_cam(self, cam: H5Cam) -> None:
        """Update the slider label"""
        assert cam is not None
        self.cam = cam
        self.cam.indexChanged.connect(self.slider.setValue)
        self.slider.setRange(0, len(self.cam.timestamps)-1)
        self.setEnabled(True)
        QTimer.singleShot(0, lambda: self.cam.reset_stream())

    def update_label(self, index: Optional[int] = None) -> None:
        """Update the time label with a new index and a timestamp

        Args:
            index (Optional[int], optional): The new frame index. Defaults to None.
        """
        if self.cam is None:
            raise ValueError("cam is None! Set it for convenient access")
        if index is not None:
            self.cam.update_index(index)

        self.__update_label_text()

    def _on_value_changed(self, value: int) -> None:
        """Update the label and emit frame index changed"""
        if self.cam is None:
            raise ValueError("cam is None! Set it for convenient access")

        if self._user_interaction or self._slider_pressed:
            self.cam.update_index(value)
            self.user_updated_slider.emit(value)

        self._user_interaction = False
        self.__update_label_text()

    def _on_slider_pressed(self) -> None:
        """User interacted with the slider"""
        self._slider_pressed = True

    def _on_slider_released(self) -> None:
        """User released the slider"""
        self._slider_pressed = False

    def __update_label_text(self) -> None:
        """Update the label text and adjust the size if necessary"""
        _new_text = f"{self.time_instance} / {self.duration}"
        _old_text = self.label.text()
        self.label.setText(_new_text)
        if len(_new_text) > len(_old_text):
            self.label.adjustSize()

    def _get_time_str(self, seconds: float) -> str:
        """Parse a duration string from the given seconds

        Args:
            seconds (float): Seconds to covert to a time string

        Returns:
            str: mm:ss or hh:mm:ss format duration string
        """
        total_seconds = np.ceil(seconds)
        total_ms = int(seconds * 1000)

        hours = int(total_seconds//3600)
        minutes = int((total_seconds % 3600)//60)
        seconds = int(total_seconds % 60)
        miliseconds = int(total_ms % 1000)

        if hours == 0:
            return f"{minutes:02}:{seconds:02}.{miliseconds:03}"
        else:
            return f"{hours:02}:{minutes:02}:{seconds:02}.{miliseconds:03}"

    @property
    def duration(self) -> str:
        """Total duration of the record"""
        if self.cam is None:
            raise ValueError("cam is None! Set the for convenient access")
        return self._get_time_str(self.cam.duration)

    @property
    def time_instance(self) -> str:
        """The exact time instance relating to the index"""
        if self.cam is None:
            raise ValueError("cam is None! Set the for convenient access")
        return self._get_time_str(self.cam.time_passed)

class VideoWidget(QWidget):
    GRAYSCALE_CMAP = ColorMap(pos=np.linspace(
        0.0, 1.0, 6), color=CMAP_GRAYSCALE)
    DISTANCE_CMAP = getFromMatplotlib('turbo')
    AMPLITUDE_CMAP = getFromMatplotlib('turbo')

    def __init__(self, parent=None,  max_display_fps=30):

        super(VideoWidget, self).__init__(parent)
        self._pending: Optional[tuple] = None  
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(max(1, int(1000 / max_display_fps)))
        self._render_timer.timeout.connect(self.flush_pending)
        self._render_timer.start()

        self.video = ImageView(self)
        self.video.ui.roiBtn.setText("Scope")
        self.pc = PointCloudWidget(self)
        self.slider = VideoSlider(parent=self)

        # Stack
        self.stacked = QStackedWidget(self)
        self.stacked.addWidget(self.video)
        self.stacked.addWidget(self.pc)

        # Handle source label
        self.source_label = QLabel("", self)
        self.source_label.setStyleSheet(
            "color: yellow; background-color: rgba(0,0,0,128); padding: 4px;")
        self.source_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.stacked.currentChanged.connect(self.update_label_position)
        self.source_label.installEventFilter(self)
        self.update_label_position()

        # Layout
        _layout = QVBoxLayout(self)
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.addWidget(self.stacked)
        _layout.addWidget(self.slider)
        self.setLayout(_layout)

    def getHistogramWidget(self) -> HistogramLUTWidget:
        if self.stacked.currentWidget() == self.pc:
            return self.pc.histogram
        else:
            return self.video.getHistogramWidget()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.source_label and event.type() == QEvent.Type.Resize:
            self.update_label_position()
        return super().eventFilter(obj, event)

    def update_label_position(self):
        """Keep the label at the bottom left"""
        current_widget = self.stacked.currentWidget()
        if not current_widget:
            return
        pos = current_widget.mapTo(self, current_widget.rect().topLeft())
        self.source_label.move(pos.x(), pos.y())

    def setActiveView(self, view: str):
        if view == 'image':
            self.stacked.setCurrentWidget(self.video)
        elif view == 'pointcloud':
            self.stacked.setCurrentWidget(self.pc)

    def flush_pending(self) -> None:
        if self._pending is not None:
            args, kwargs = self._pending
            self._pending = None
            self._updateView(*args, **kwargs)

    def setImage(self, *args, **kwargs):
        self._pending = (args, kwargs)

    def _updateView(self, *args, **kwargs):
        data = args[0]
        if self.stacked.currentWidget() == self.video and isinstance(data, np.ndarray):
            self.video.setImage(*args, **kwargs)
        elif self.stacked.currentWidget() == self.pc and isinstance(data, tuple):
            autolevels = kwargs.get('autoLevels', False)
            self.pc.update_point_cloud(data, autolevels)

    def setColorMap(self, cmap):
        self.video.setColorMap(cmap)

    def setLevels(self, min, max):
        self.getHistogramWidget().setLevels(min, max)

    def reset(self) -> None:
        """Set the blank screen"""
        if self.stacked.currentWidget() == self.video:
            _image = self.video.imageItem.image
            self.video.setImage(np.zeros_like(_image))
        else:
            self.pc.update_point_cloud((np.zeros(3), np.zeros(3)))  # type: ignore

        self.slider.setVisible(False)
