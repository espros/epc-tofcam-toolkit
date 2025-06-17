import importlib.resources
import time
from pathlib import Path
from typing import Optional, Type

import numpy as np
from epc.tofCam_gui.widgets import MenuBar, ToolBar, VideoWidget
from epc.tofCam_gui.widgets.console_widget import Console_Widget
from epc.tofCam_lib import TOFcam
from epc.tofCam_lib.h5Cam import H5Cam
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                               QMainWindow, QMessageBox, QSplashScreen,
                               QVBoxLayout, QWidget)


class Base_GUI_TOFcam(QMainWindow):

    def __init__(self, title: str, parent=None):
        from epc.tofCam_gui.gui_tofCams_bridge import Base_TOFcam_Bridge

        super(Base_GUI_TOFcam, self).__init__()
        self._show_splash_screen()
        self.setWindowTitle(title)

        self.time_last_frame = time.time()
        self.time_last_update = time.time()
        self._fps = 0.0
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
        self.toolBar.importButton.toggled.connect(self._import_toggled)
        self.toolBar.importButton.triggered.connect(
            self._connect_replay_source)

        self.bridge: Optional[Base_TOFcam_Bridge] = None

    def _import_toggled(self) -> None:
        QTimer.singleShot(0, lambda: self.toolBar.playButton.setEnabled(
            not self.toolBar.importButton.isChecked()))
        QTimer.singleShot(0, lambda: self.toolBar.captureButton.setEnabled(
            not self.toolBar.importButton.isChecked()))
        QTimer.singleShot(0, lambda: self.toolBar.recordButton.setEnabled(
            not self.toolBar.importButton.isChecked()))

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

    def setSettingsEnabled(self, enabled: bool):
        for i in range(self.settingsLayout.count()):
            widget = self.settingsLayout.itemAt(i).widget()
            if widget:
                widget.setEnabled(enabled)

    def _save_raw(self):
        filePath, _ = QFileDialog.getSaveFileName(
            self, 'Save raw', filter='*.raw')
        test = self.imageView.video.getImageItem().image
        np.savetxt(filePath + '.csv', test, delimiter=',')

    def _save_png(self):
        filePath, _ = QFileDialog.getSaveFileName(
            self, 'Save png', filter='*.png')
        self.imageView.video.getImageItem().save(filePath + '.png')

    def _show_splash_screen(self, image_path=importlib.resources.files('epc.tofCam_gui.icons').joinpath('epc-logo.png')):
        splash_pix = QPixmap(image_path)
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

    def _connect_H5Cam(self) -> Optional[H5Cam]:
        """Connect the source h5 file to interract with"""
        _success = False
        _recorded_stream, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select recorded stream",
            dir="",
            filter="H5 Files (*.h5);;All Files (*)"
        )
        if _recorded_stream is None:
            QMessageBox.warning(
                self, "No file selected", "Select a recorded stream `*.h5`!")

        elif Path(_recorded_stream).is_dir():
            QMessageBox.warning(
                self, "Directory selected", "Please select a standalone `*.h5` file!")

        elif Path(_recorded_stream).suffix != ".h5":
            QMessageBox.warning(self, "Wrong file selected",
                                f"`{_recorded_stream}` is not valid! Recorded stream file should have the extension `.h5`")

        else:
            confirm = QMessageBox.question(self,
                                           "Recorded stream selected",
                                           f"`{_recorded_stream}` will be replayed. Do you confirm?",
                                           buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                           defaultButton=QMessageBox.StandardButton.Yes)

            if confirm == QMessageBox.StandardButton.Yes:
                cam = H5Cam(_recorded_stream, continuous=False)
                self._set_bridge(cam)
                _success = True
                return cam

        if not _success:
            QTimer.singleShot(100, self.toolBar.importButton.toggle)

        return None

    def _disconnect_H5Cam(self) -> None:
        """Revert the replay source connection"""
        assert self.bridge is not None
        if self.imageView.slider.playButton.isChecked():
            self.imageView.slider.playButton.click()
        try:
            self.bridge._fallback()
        except:
            self.bridge.disconnect()
            QTimer.singleShot(
                100, lambda: self.toolBar.playButton.setEnabled(False))
            QTimer.singleShot(
                100, lambda: self.toolBar.captureButton.setEnabled(False))
            QTimer.singleShot(
                100, lambda: self.toolBar.recordButton.setEnabled(False))

    def _connect_replay_source(self, enable: bool) -> None:
        """Select the binary file and update the firmware"""
        if enable:
            self._connect_H5Cam()
        else:
            self._disconnect_H5Cam()

    def _set_bridge(self, cam: TOFcam, _bridge_type: Optional[Type["Base_TOFcam_Bridge"]] = None) -> None:
        if self.bridge is None:
            if _bridge_type is None:
                raise ValueError("Define the bridge GUI specific bridge type!")
            self.bridge = _bridge_type(cam=cam, gui=self)
        else:
            self.bridge._update_cam(cam)


def main():
    import sys

    from PySide6 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)

    stream = Base_GUI_TOFcam(title="Base")
    stream.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
