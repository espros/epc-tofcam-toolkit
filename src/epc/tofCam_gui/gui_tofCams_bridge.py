from copy import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from epc.tofCam_gui import Base_GUI_TOFcam
from epc.tofCam_gui.data_logger import HDF5Logger
from epc.tofCam_gui.streamer import Streamer
from epc.tofCam_lib import TOFcam
from epc.tofCam_lib.h5Cam import H5Cam
from PySide6.QtWidgets import QFileDialog, QMessageBox


class Base_TOFcam_Bridge():

    MAX_AMPLITUDE = 0  # needs to be overwritten by the derived class
    MAX_GRAYSCALE = 0  # needs to be overwritten by the derived class
    MIN_DCS = -2048
    MAX_DCS = 2047

    def __init__(self, cam: TOFcam, gui: Base_GUI_TOFcam) -> None:
        """

        Args:
            cam (TOFcam): The camera to bridge with the gui
            gui (Base_GUI_TOFcam): The gui to bridge with the camera
        """

        self.gui = gui
        self.data_logger: Optional[HDF5Logger] = None

        self.image_type = 'Distance'
        self._distance_unambiguity = None  # needs to be overwritten by the derived class
        self.streamer = Streamer(lambda: np.ndarray([]))

        # connect signals
        self.gui.toolBar.captureButton.triggered.connect(self.capture)
        self.gui.toolBar.playButton.triggered.connect(self._set_streaming)
        self.gui.imageView.slider.playButton.clicked.connect(
            self._set_replay_streaming)
        self.gui.toolBar.recordButton.triggered.connect(self._set_recording)

        self._static_meta: Dict[str, Any] = {}
        self.fallback_cam: Optional[TOFcam] = None
        self.fallback_source = ""
        self.cam = cam
        self._update_cam(cam=cam) 
        self.gui.bridge = self

    def _update_cam(self, cam: TOFcam) -> None:
        self.fallback_cam = self.cam
        self.fallback_source = self.gui.imageView.source_label.text()
        self.cam = cam
        self._get_image_cb = cam.get_distance_image

        # update chip information
        chipID, waferId = cam.device.get_chip_infos()
        self.gui.toolBar.setChipInfo(chipID, waferId)

        fw_version = cam.device.get_fw_version()
        self.gui.toolBar.setVersionInfo(fw_version)

        self.gui.topMenuBar.openConsoleAction.triggered.connect(
            lambda: self.gui.console.startup_kernel(cam))

        self.gui.setDefaultValues()

        if isinstance(cam, H5Cam):

            if hasattr(self, "_set_image_type") and hasattr(self.gui, "imageTypeWidget"):
                self._set_image_type(cam.image_type)
                self.gui.imageTypeWidget.comboBox.setCurrentText(
                    cam.image_type)

            self.streamer = Streamer(self.getImage, post_stop_cb=self.capture)
            self.gui.imageView.slider.setVisible(True)
            self.gui.imageView.source_label.setText(f"{cam.source}")
            self.gui.imageView.source_label.adjustSize()
            self.gui.imageView.slider.update_cam(cam)
            self.gui.imageView.slider.user_updated_slider.connect(
                self._slider_handler)
            self.gui.setSettingsEnabled(False)

        else:
            self.fallback_cam = None
            self.fallback_source = ""
            self.gui.setSettingsEnabled(True)
            self.gui.imageView.slider.setVisible(False)
            self.streamer = Streamer(self.getImage)

        self.streamer.signal_new_frame.connect(self.updateImage)
        self.streamer.signal_new_frame.connect(self.storeImage)
        self.capture()

        # Fetch meta
        self._static_meta = {
            "chipid": chipID,
            "waferid": waferId,
            "chip_infos": (chipID, waferId),
            "fw_version": fw_version,
        }

    def _fallback(self) -> None:
        """Connect the fallback camera"""
        assert self.fallback_cam is not None
        self.gui.imageView.source_label.setText(f"{self.fallback_source}")
        self.cam, self.fallback_cam = self.fallback_cam, self.cam  # Switch, python way
        self._update_cam(self.cam)
        self.gui.imageView.source_label.adjustSize()
        self.gui.imageView.update_label_position()

    def disconnect(self) -> None:
        self.streamer.stop_stream()
        self.gui.imageView.reset()

        self.streamer.deleteLater()
        self.streamer = Streamer(lambda: np.ndarray([]))

    def capture(self, mode=0):
        image = self.getImage()
        self.gui.updateImage(image)

    def updateImage(self, image):
        if self.streamer.is_streaming():
            self.gui.updateImage(image)

    def storeImage(self, image):
        if self.data_logger is not None:
            if self.data_logger.is_running():
                if self._get_image_cb.__func__ is self.get_combined_dcs.__func__:
                    image = self._unroll_combined_dcs(image)
                self.data_logger.add_frame(image)

    def getImage(self):
        return self._get_image_cb()

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
        dcs = self.cam.get_raw_dcs_images()
        image = self._combine_dcs(dcs)
        return image

    def _set_streaming(self, enable: bool) -> None:
        if enable:
            self.streamer.start_stream()
        else:
            self.streamer.stop_stream()

    def _set_replay_streaming(self, enable: bool) -> None:
        if isinstance(self.cam, H5Cam):
            if enable:
                self.cam.enable_continous(True)
                self.streamer.start_stream()
            else:
                self.cam.enable_continous(False)
                self.streamer.stop_stream()

    def _set_recording(self, enable: bool) -> None:
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
            self._get_image_cb = self.cam.get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self._distance_unambiguity*1000)
        elif image_type == 'Amplitude':
            self.gui.imageView.setActiveView('image')
            self._get_image_cb = self.cam.get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif image_type == 'Grayscale':
            self.gui.imageView.setActiveView('image')
            self._get_image_cb = self.cam.get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        elif image_type == 'DCS':
            self.gui.imageView.setActiveView('image')
            self._get_image_cb = self.get_combined_dcs
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(self.MIN_DCS, self.MAX_DCS)
        else:
            raise ValueError(f"Image type '{image_type}' is not supported")

    def _start_recording(self) -> None:
        _success = False
        _dev_id = ""

        try:
            _cid, _wid = self.cam.device.get_chip_infos()
            _dev_id = f"_w{_wid:03}c{_cid:03}"
        except:
            pass

        _img_type = self.image_type.lower().replace(" ", "_")
        _date = datetime.now().strftime("%y%m%d_%H%M%S")

        default_name = datetime.now().strftime(
            f"{_img_type}{_dev_id}_{_date}.h5")

        filepath, _ = QFileDialog.getSaveFileName(
            self.gui,
            "Save Recording As…",
            default_name,
            "HDF5 Files (*.h5)"
        )
        if filepath is None:
            QMessageBox.warning(
                self.gui, "No file set", "Set a valid target`*.h5`!")

        elif Path(filepath).is_dir():
            QMessageBox.warning(
                self.gui, "Directory set", "Please set a standalone `*.h5` filename!")

        elif Path(filepath).suffix != ".h5":
            QMessageBox.warning(self.gui, "Wrong format set",
                                f"`{filepath}` is not valid! Recorded stream file should have the extension `.h5`")

        else:

            if not self.streamer.is_streaming():
                self.gui.toolBar.playButton.trigger()

            # initialize the logger
            self.data_logger = HDF5Logger(self.image_type, filepath)

            self.data_logger.set_metadata(**self.metadata)
            self.data_logger.start()
            self.gui.setSettingsEnabled(False)
            _success = True

        if not _success:
            self.gui.toolBar.recordButton.toggle()

    def _stop_recording(self):
        if self.data_logger is not None:
            self.data_logger.stop_logging()
            self.data_logger.wait()
            self.gui.setSettingsEnabled(True)

    def _slider_handler(self, val: int) -> None:
        if not isinstance(self.cam, H5Cam):
            raise NotImplementedError(
                f"Slide handler is only available for H5Cam! Not for {self.cam.__class__.__name__}")

        if self.gui.imageView.slider.playButton.isChecked():
            self.gui.imageView.slider.playButton.click()
        self.cam.update_index(val)
        self.capture()

    @property
    def metadata(self) -> dict[str, object]:
        # Operation metadata
        __meta = copy(self._static_meta)
        __meta["image_type"] = self.image_type

        __meta.update({
            "image_type": self.image_type,
            "roi": self.cam.settings.get_roi()})

        if hasattr(self.cam, "mod_frequency"):
            __meta["mod_frequency"] = self.cam.mod_frequency

        return __meta
