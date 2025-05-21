import time
from datetime import datetime

import numpy as np
from PySide6.QtWidgets import QFileDialog

from epc.tofCam_gui import Base_GUI_TOFcam
from epc.tofCam_gui.data_logger import HDF5Logger
from epc.tofCam_gui.streamer import Streamer, pause_streaming
from epc.tofCam_lib import TOFcam


class Base_TOFcam_Bridge():

    MAX_AMPLITUDE = 0  # needs to be overwritten by the derived class
    MAX_GRAYSCALE = 0  # needs to be overwritten by the derived class
    MIN_DCS = -2048
    MAX_DCS = 2047

    def __init__(self, cam: TOFcam, gui: Base_GUI_TOFcam):
        self.cam = cam
        self.gui = gui
        self.data_logger = None

        self.image_type = 'Distance'
        self._distance_unambiguity = None  # needs to be overwritten by the derived class
        self._get_image_cb = cam.get_distance_image

        self.streamer = Streamer(self.getImage)
        self.streamer.signal_new_frame.connect(self.updateImage)

        # update chip information
        chipID, waferId = cam.device.get_chip_infos()
        gui.toolBar.setChipInfo(chipID, waferId)
        fw_version = cam.device.get_fw_version()
        gui.toolBar.setVersionInfo(fw_version)

        # connect signals
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.toolBar.playButton.triggered.connect(self._set_streaming)
        gui.toolBar.recordButton.triggered.connect(self._set_recording)
        gui.topMenuBar.openConsoleAction.triggered.connect(
            lambda: gui.console.startup_kernel(cam))

        # gui.topMenuBar.startRecordingAction.triggered.connect(
        #     self._start_recording)
        # gui.topMenuBar.stopRecordingAction.triggered.connect(
        #     self._stop_recording)

        # connect signals between play & data record
        gui.topMenuBar.stopRecordingAction.triggered.connect(
            lambda _: gui.toolBar.playButton.trigger()
        )
        gui.toolBar.playButton.triggered.connect(
            lambda enabled: self._stop_recording() if not enabled else None)

    def capture(self, mode=0):
        image = self.getImage()
        self.gui.updateImage(image)

    def updateImage(self, image):
        if self.streamer.is_streaming():
            self.gui.updateImage(image)
        if self.data_logger != None and self.data_logger.is_running():
            self.data_logger.add_frame(image.copy(), time.time())

    def getImage(self):
        return self._get_image_cb()

    def get_combined_dcs(self):
        dcs = self.cam.get_raw_dcs_images()
        resolution = np.array(dcs.shape[1:])
        image = np.zeros(2*resolution)
        image[0:resolution[0], 0:resolution[1]] = dcs[0]
        image[0:resolution[0], resolution[1]:] = dcs[1]
        image[resolution[0]:, 0:resolution[1]] = dcs[2]
        image[resolution[0]:, resolution[1]:] = dcs[3]
        return image

    def _set_streaming(self, enable: bool):
        if enable:
            self.streamer.start_stream()
        else:
            self.streamer.stop_stream()

    def _set_recording(self, enable: bool):
        if enable:
            self._start_recording()
        else:
            self._stop_recording()

    def _set_standard_image_type(self, image_type: str):
        """ Set the image type to the given type and update the GUI accordingly """
        self.image_type = image_type
        if image_type == 'Distance':
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
        if self.data_logger is None:
            return
        self.data_logger.stop_logging()
        self.data_logger.wait()
        self.gui.setSettingsEnabled(True)
        self.gui.topMenuBar.startRecordingAction.setEnabled(True)
        self.gui.topMenuBar.stopRecordingAction.setEnabled(False)
