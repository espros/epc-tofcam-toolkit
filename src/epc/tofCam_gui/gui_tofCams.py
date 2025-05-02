import time

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                               QMainWindow, QSplashScreen, QVBoxLayout,
                               QWidget)

from epc.tofCam_gui.config import EPC_LOGO
from epc.tofCam_gui.data_logger import HDF5Logger
from epc.tofCam_gui.widgets import MenuBar, ToolBar, VideoWidget, RoiSettings, GroupBoxSelection
from epc.tofCam_gui.widgets.console_widget import Console_Widget


class Base_GUI_TOFcam(QMainWindow):

    frame_ready = Signal(np.ndarray, float)

    def __init__(self, title: str, parent=None):
        super(Base_GUI_TOFcam, self).__init__()
        self._show_splash_screen()
        self.setWindowTitle(title)

        self.time_last_frame = time.time()
        self.time_last_update = time.time()
        self._fps = 0
        self.__filter_cb = None

        # create main widgets
        self.toolBar = ToolBar(self)
        self.topMenuBar = MenuBar(self)
        self.imageView = VideoWidget()
        self.settingsLayout = QVBoxLayout()
        self.mainLayout = QGridLayout()
        self.widget = QWidget()
        self.console = Console_Widget()

        self.addToolBar(self.toolBar)
        self.setMenuBar(self.topMenuBar)

        self.topMenuBar.saveRawAction.triggered.connect(self._save_raw)
        self.topMenuBar.savePngAction.triggered.connect(self._save_png)
        self.topMenuBar.setDefaultValuesAction.triggered.connect(
            self.setDefaultValues)

        self.topMenuBar.startRecordingAction.triggered.connect(
            self._start_recording)
        self.topMenuBar.stopRecordingAction.triggered.connect(
            self._stop_recording)

    def complete_setup(self):
        """ ! needs to be called at the end of the __init__ method of the derived class !
        """
        self.mainLayout.setSpacing(10)
        self.mainLayout.addLayout(self.settingsLayout, 0, 0)
        self.mainLayout.addWidget(self.imageView, 0, 1)
        self.mainLayout.setColumnStretch(1, 3)

        self.widget.setLayout(self.mainLayout)
        self.setCentralWidget(self.widget)

        self.resize(1200, 600)

        self.setDefaultValues()

    def setDefaultValues(self):
        for i in range(self.settingsLayout.count()):
            widget = self.settingsLayout.itemAt(i).widget()
            if widget and hasattr(widget, 'setDefaultValue'):
                widget.setDefaultValue()

    def _save_raw(self):
        filePath, _ = QFileDialog.getSaveFileName(
            self, 'Save raw', filter='*.raw')
        test = self.imageView.video.getImageItem().image
        np.savetxt(filePath + '.csv', test, delimiter=',')

    def _save_png(self):
        filePath, _ = QFileDialog.getSaveFileName(
            self, 'Save raw', filter='*.png')
        self.imageView.video.getImageItem().save(filePath + '.png')

    def _start_recording(self):

        #  find current image type from the GUI widgets
        image_type = ""
        for i in range(self.settingsLayout.count()):
            widget = self.settingsLayout.itemAt(i).widget()
            if isinstance(widget, GroupBoxSelection):
                image_type = widget.getSelection()

        # initialize the logger
        self.data_logger = HDF5Logger(image_type)
        metadata = self._set_recording_metadata()
        if metadata:
            self.data_logger.set_metadata(**metadata)
        self.frame_ready.connect(self.data_logger.add_frame)
        self.data_logger.start()
        self.topMenuBar.startRecordingAction.setEnabled(False)
        self.topMenuBar.stopRecordingAction.setEnabled(True)

    def _stop_recording(self):
        self.frame_ready.disconnect(self.data_logger.add_frame)
        self.data_logger.stop_logging()
        self.data_logger.wait()
        self.topMenuBar.startRecordingAction.setEnabled(True)
        self.topMenuBar.stopRecordingAction.setEnabled(False)

    def _set_recording_metadata(self) -> dict[str, object]:
        """
        override by subclasses to supply recording metadata.
        returns a dict of {metadata_name: value}. Default is empty.
        """
        return {}

    def _show_splash_screen(self, image_path=EPC_LOGO):
        splash_pix = QPixmap(str(image_path))
        self.splash = QSplashScreen(splash_pix)
        self.splash.show()
        self.splash.raise_()
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def show(self) -> None:
        super().show()
        self.splash.finish(self)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.console.close()
        return super().closeEvent(event)

    def setFilter_cb(self, filter_cb):
        self.__filter_cb = filter_cb

    def updateImage(self, image):
        time_diff = time.time() - self.time_last_frame
        t_update_diff = time.time() - self.time_last_update
        if time_diff != 0:
            fps = round(1 / time_diff)
            if fps < 100:
                self._fps = 0.2 * self._fps + 0.8 * fps  # low pass filter fps
            self.toolBar.setFPS(self._fps)
        self.time_last_frame = time.time()

        # prevent gui from freezing on high fps
        if t_update_diff < 0.2:
            return
        self.time_last_update = time.time()

        if self.__filter_cb:
            image = self.__filter_cb(image)
        self.imageView.setImage(image, autoRange=False,
                                autoHistogramRange=False, autoLevels=False)

        self.frame_ready.emit(image.copy(), time.time())
