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
        self.gui.toolBar.replayButton.triggered.connect(self._set_streaming)
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
        self.gui.setDefaultValues()

        # Fetch meta
        self._meta = {
            "roi": cam.settings.get_roi(),
            "chip_infos": (chipID, waferId),
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
            if self.data_logger != None and self.data_logger.is_running():
                self.data_logger.add_frame(image.copy(), time.time())

    def getImage(self):
        if self.cam is not None:
            return self._get_image_cb()
        else:
            return lambda: np.ndarray([])

    def get_combined_dcs(self):
        if self.cam is not None:
            dcs = self.cam.get_raw_dcs_images()
            resolution = np.array(dcs.shape[1:])
            image = np.zeros(2*resolution)
            image[0:resolution[0], 0:resolution[1]] = dcs[0]
            image[0:resolution[0], resolution[1]:] = dcs[1]
            image[resolution[0]:, 0:resolution[1]] = dcs[2]
            image[resolution[0]:, resolution[1]:] = dcs[3]
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
                    self._bridge_cam(H5Cam(_recorded_stream))
                    self.gui.imageView.setActiveView('image')
                    _success = True

            if not _success:
                QTimer.singleShot(100, self.gui.toolBar.importButton.toggle)
        else:
            if hasattr(self, "prev_cam"):
                self.cam = self.prev_cam
                self._bridge_cam(self.cam)
