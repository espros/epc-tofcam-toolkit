import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from coap.common import Coap_Settings  # type: ignore
from epc.tofCam_gui import Base_GUI_TOFcam
from epc.tofCam_gui.data_logger import HDF5Logger
from epc.tofCam_gui.streamer import Streamer
from epc.tofCam_lib import TOFcam
from epc.tofCam_lib.h5Cam import H5_Settings_Controller, H5Cam
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox


class Base_TOFcam_Bridge():

    MAX_AMPLITUDE = 0  # needs to be overwritten by the derived class
    MAX_GRAYSCALE = 0  # needs to be overwritten by the derived class
    MIN_DCS = -2048
    MAX_DCS = 2047

    def __init__(self, cam: Optional[TOFcam], gui: Base_GUI_TOFcam):

        self.gui = gui
        self.data_logger: Optional[HDF5Logger] = None

        self.image_type = 'Distance'
        self._distance_unambiguity = None  # needs to be overwritten by the derived class
        self.streamer = Streamer(lambda: np.ndarray([]))

        # connect signals
        self.gui.toolBar.captureButton.triggered.connect(self.capture)
        self.gui.toolBar.playButton.triggered.connect(self._set_streaming)
        self.gui.imageView.slider.playButton.clicked.connect(
            self._set_streaming)
        self.gui.toolBar.recordButton.triggered.connect(self._set_recording)
        self.gui.toolBar.importButton.triggered.connect(self._replay)

        self._meta: Dict[str, Any] = {}

        if cam is not None:
            self._bridge_cam(cam=cam)

        self.cam = cam

    def _bridge_cam(self, cam: Optional[TOFcam]) -> None:
        assert cam is not None
        self._get_image_cb = cam.get_distance_image

        # update chip information
        chipID, waferId = cam.device.get_chip_infos()
        self.gui.toolBar.setChipInfo(chipID, waferId)

        fw_version = cam.device.get_fw_version()
        self.gui.toolBar.setVersionInfo(fw_version)

        self.gui.topMenuBar.openConsoleAction.triggered.connect(
            lambda: self.gui.console.startup_kernel(cam))

        # Set the cam and get the streamer
        self.cam = cam
        self.streamer = Streamer(self.getImage)
        self.streamer.signal_new_frame.connect(self.updateImage)
        self.streamer.signal_new_frame.connect(self.storeImage)
        self.gui.setDefaultValues()

        # Fetch meta
        self._meta = {
            "chipid": chipID,
            "waferid": waferId,
            "chip_infos": (chipID, waferId),
            "roi": cam.settings.get_roi(),
            "fw_version": fw_version,
        }

        if isinstance(cam.settings, Coap_Settings) or isinstance(cam.settings, H5_Settings_Controller):
            self._meta.update(
                {"mod_frequency": cam.settings.get_modulation(),
                 }
            )

    def capture(self, mode=0):
        if self.cam is not None:
            image = self.getImage()
            self.gui.updateImage(image)

    def updateImage(self, image):
        if self.cam is not None:
            if self.streamer.is_streaming():
                self.gui.updateImage(image)
                if isinstance(self.cam, H5Cam):
                    self.gui.imageView.slider.blockSignals(True)
                    self.gui.imageView.slider.slider.setValue(self.cam.index)
                    self.gui.imageView.slider.update_label(self.cam.index)
                    self.gui.imageView.slider.blockSignals(False)

    def storeImage(self, image):
        if self.data_logger is not None:
            if self.data_logger.is_running():
                if self._get_image_cb.__func__ is self.get_combined_dcs.__func__:
                    image = self._unroll_combined_dcs(image)
                self.data_logger.add_frame(image)

    def getImage(self):
        if self.cam is not None:
            return self._get_image_cb()
        else:
            return lambda: np.ndarray([])

    @staticmethod
    def _combine_dcs(frame: np.ndarray) -> np.ndarray:
        """Combine the dcs frames in one frame"""
        resolution = np.array(frame.shape[1:])
        image = np.zeros(2*resolution)

        image[0:resolution[0], 0:resolution[1]] = frame[0]
        image[0:resolution[0], resolution[1]:] = frame[1]
        image[resolution[0]:, 0:resolution[1]] = frame[2]
        image[resolution[0]:, resolution[1]:] = frame[3]

        return image

    @staticmethod
    def _unroll_combined_dcs(image: np.ndarray) -> np.ndarray:
        """Unroll the combined dcs frame to it's components"""
        height = image.shape[0]//2
        width = image.shape[1]//2
        frame = np.zeros((4, height, width), dtype=image.dtype)

        frame[0] = image[0:height, 0:width]
        frame[1] = image[0:height, width:2*width]
        frame[2] = image[height:2*height, 0:width]
        frame[3] = image[height:2*height, width:2*width]

        return frame

    def get_combined_dcs(self):
        if self.cam is not None:
            dcs = self.cam.get_raw_dcs_images()
            image = self._combine_dcs(dcs)
            return image
        else:
            return np.ndarray([])

    def _set_streaming(self, enable: bool) -> None:
        if self.cam is not None:
            if enable:
                self.streamer.start_stream()
            else:
                self.streamer.stop_stream()

    def _set_recording(self, enable: bool) -> None:
        if self.cam is not None:
            if enable:
                self._start_recording()
            else:
                self._stop_recording()

    def _set_standard_image_type(self, image_type: str):
        """ Set the image type to the given type and update the GUI accordingly """
        self.image_type = image_type
        if image_type == 'Distance':
            assert self._distance_unambiguity is not None
            self.gui.imageView.setActiveView('image')
            if self.cam is not None:
                self._get_image_cb = self.cam.get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self._distance_unambiguity*1000)
        elif image_type == 'Amplitude':
            self.gui.imageView.setActiveView('image')
            if self.cam is not None:
                self._get_image_cb = self.cam.get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif image_type == 'Grayscale':
            self.gui.imageView.setActiveView('image')
            if self.cam is not None:
                self._get_image_cb = self.cam.get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        elif image_type == 'DCS':
            self.gui.imageView.setActiveView('image')
            if self.cam is not None:
                self._get_image_cb = self.get_combined_dcs
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(self.MIN_DCS, self.MAX_DCS)
        else:
            raise ValueError(f"Image type '{image_type}' is not supported")

    def _start_recording(self):

        # file dialog for data save
        default_name = datetime.now().strftime("data_%Y%m%d_%H%M%S.h5")
        filepath, _ = QFileDialog.getSaveFileName(
            self.gui,
            "Save Recording As…",
            default_name,
            "HDF5 Files (*.h5)"
        )
        if not filepath:
            return

        if not self.streamer.is_streaming():
            self.gui.toolBar.playButton.trigger()

        # initialize the logger
        self.data_logger = HDF5Logger(self.image_type, filepath)
        metadata = self.gui._set_recording_metadata()
        if metadata:
            self.data_logger.set_metadata(**metadata)
        self.data_logger.start()
        self.gui.setSettingsEnabled(False)
        self.gui.topMenuBar.startRecordingAction.setEnabled(False)
        self.gui.topMenuBar.stopRecordingAction.setEnabled(True)

    def _stop_recording(self):
        if self.data_logger is not None:
            self.data_logger.stop_logging()
            self.data_logger.wait()
            self.gui.setSettingsEnabled(True)
            self.gui.topMenuBar.startRecordingAction.setEnabled(True)
            self.gui.topMenuBar.stopRecordingAction.setEnabled(False)

    def _replay(self, enable: bool) -> None:
        """Select the binary file and update the firmware"""
        _success = False
        if enable:
            _recorded_stream, _ = QFileDialog.getOpenFileName(
                parent=self.gui,
                caption="Select recorded stream",
                dir="",
                filter="H5 Files (*.h5);;All Files (*)"
            )
            if _recorded_stream is None:
                QMessageBox.warning(
                    self.gui, "No file selected", "Select a recorded stream `*.h5`!")

            elif Path(_recorded_stream).is_dir():
                QMessageBox.warning(
                    self.gui, "Directory selected", "Please select a standalone `*.h5` file!")

            elif Path(_recorded_stream).suffix != ".h5":
                QMessageBox.warning(self.gui, "Wrong file selected",
                                    f"`{_recorded_stream}` is not valid! Recorded stream file should have the extension `.h5`")

            else:
                confirm = QMessageBox.question(self.gui,
                                               "Recorded stream selected",
                                               f"`{_recorded_stream}` will be replayed. Do you confirm?",
                                               buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                               defaultButton=QMessageBox.StandardButton.Yes)

                if confirm == QMessageBox.StandardButton.Yes:
                    if hasattr(self, "cam"):
                        self.prev_cam = self.cam
                        self.prev_source = self.gui.imageView.source_label.text()
                    cam = H5Cam(_recorded_stream)

                    def _get_frame(idx: int):
                        cam.update_index(idx)
                        self.capture()

                    self._bridge_cam(cam)
                    self.gui.imageView.setActiveView('image')
                    self.gui.imageView.slider.setVisible(True)
                    QTimer.singleShot(
                        100, self.gui.imageView.update_label_position)
                    self.gui.imageView.slider.update_record(cam.timestamps)
                    self.gui.imageView.slider.frame_idx_changed.connect(
                        _get_frame)
                    self.gui.imageView.source_label.setText(f"{cam.source}")
                    self.gui.imageView.source_label.adjustSize()
                    QTimer.singleShot(
                        0, self.gui.imageView.slider.playButton.click)
                    _success = True

            if not _success:
                QTimer.singleShot(100, self.gui.toolBar.importButton.toggle)
        else:
            image = self.getImage()
            self.gui.updateImage(np.zeros_like(image))
            if self.gui.imageView.slider.playButton.isChecked():
                self.gui.imageView.slider.playButton.click()
            if hasattr(self, "prev_cam"):
                self.cam = self.prev_cam
                self.gui.imageView.source_label.setText(f"{self.prev_source}")
                self.gui.imageView.source_label.adjustSize()
                if self.cam is not None:
                    self._bridge_cam(self.cam)
                self.gui.imageView.slider.setVisible(False)
                QTimer.singleShot(
                    100, self.gui.imageView.update_label_position)
