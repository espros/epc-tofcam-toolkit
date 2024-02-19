from epc.tofCam635 import TofCam635
from epc.tofCam_gui.gui_tofCam635 import GUI_TOFcam635
from epc.tofCam_gui.settings_widget import IntegrationTimes, IntegrationTimes635
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import qdarktheme
import time

class TofCam635Bridge:
    DEFAULT_INT_TIME_GRAY = 100
    DEFAULT_INT_TIME_DIST = 1000
    MAX_DISTANCE = 15000
    MAX_AMPLITUDE = 2896
    MAX_GRAYSCALE = 0xFF

    def __init__(self, gui: GUI_TOFcam635, cam: TofCam635) -> None:
        self.gui = gui
        self.cam = cam
        self.getImage_cb = None
        self.__is_streaming = False

        cam.cmd.setOperationMode(0)

        self.time_last_frame = time.time()
        self.frameTimer = QTimer()
        self.frameTimer.timeout.connect(self.capture)
        self.gui.toolBar.playButton.triggered.connect(lambda: self.setStreaming(self.gui.toolBar.playButton.isChecked()))
        self.gui.integrationTimes.signal_value_changed.connect(self._update_int_time)
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.imageTypeWidget.selection_changed_signal.connect(self._changeImageType)
        gui.hdrModeDropDown.signal_selection_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(lambda value: self._set_min_amplitudes(value))

        gui.builtInFilter.medianFilter.signal_filter_changed.connect(lambda enable: self.cam.cmd.setMedianFilter(enable))
        gui.builtInFilter.temporalFilter.signal_filter_changed.connect(lambda enable, threshold, factor: self.cam.cmd.setTemporalFilter(enable, threshold, factor))
        gui.builtInFilter.averageFilter.signal_filter_changed.connect(lambda enable: self.cam.cmd.setAverageFilter(enable))
        gui.builtInFilter.edgeFilter.signal_filter_changed.connect(lambda enable, threshold: self.cam.cmd.setEdgeFilter(enable, threshold))
        gui.roiSettings.signal_roi_changed.connect(lambda x, y, w, h: self.cam.set_roi(x, y, w, h))

        self.updateChipID()
        self._changeImageType(gui.imageTypeWidget.comboBox.currentText())

    def setStreaming(self, enable=True):
        self.__is_streaming = enable
        self.__stream()

    def __stream(self):
        if self.__is_streaming:
            QTimer.singleShot(10, self.__stream)
            self.capture()

    def _set_min_amplitudes(self, minAmp: int):
        for i in range(5):
            self.cam.cmd.setAmplitudeLimit(i, minAmp)

    def _set_hdr_mode(self, mode: str):
        if mode == 'HDR Spatial':
            self.gui.integrationTimes.set_normal_mode()
            self.cam.cmd.setHDR('spatial')
        elif mode == 'HDR Temporal':
            self.gui.integrationTimes.set_hdr_mode()
            self.cam.cmd.setHDR('temporal')
        elif mode == 'HDR Off':
            self.gui.integrationTimes.set_normal_mode()
            self.cam.cmd.setHDR('off')
        else:
            raise ValueError(f"HDR Mode '{mode}' not supported")

    def _update_int_time(self, type: str, intTime: int):
        if   type == 'WFOV1':
            self.cam.cmd.setIntTimeDist(0, intTime)
        elif type == 'WFOV2':
            self.cam.cmd.setIntTimeDist(1, intTime)
        elif type == 'WFOV3':
            self.cam.cmd.setIntTimeDist(2, intTime)
        elif type == 'WFOV4':
            self.cam.cmd.setIntTimeDist(3, intTime)
        elif type == 'NFOV':
            self.cam.cmd.setIntTimeDist(4, intTime)
        elif type == 'Gray':
            self.cam.cmd.setIntTimeGray(0, intTime)
        elif type == 'auto':
            if intTime == 1:
                self.cam.cmd.setIntTimeDist(0xFF, intTime)
            else:
                self.cam.cmd.setIntTimeDist(0, self.gui.integrationTimes.wFOV[0].value())
        else:
            raise ValueError(f"Integration Time Type '{type}' not supported")

    def __get_grayscale_image(self):
        return self.cam.get_grayscale_image()

    def __get_distance_image(self):
        return self.cam.get_distance_image()

    def __get_amplitude_image(self):
        return self.cam.get_amplitude_image()

    def _changeImageType(self, imgType: str):
        self.imageType = imgType
        if imgType == 'Distance':
            self.getImage_cb = self.__get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_DISTANCE)
        elif imgType == 'Amplitude':
            self.getImage_cb = self.__get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif imgType == 'Grayscale':
            self.getImage_cb = self.__get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        else:
            raise ValueError(f"Image Type '{imgType}' not supported")
        self.capture()

    def updateChipID(self):
        self.gui.toolBar.setChipInfo(*self.cam.cmd.getChipInfo())

    def capture(self):
        fps = round(1 / (time.time() - self.time_last_frame))
        self.time_last_frame = time.time()

        image = self.getImage_cb()
        self.gui.imageView.setImage(image, autoRange=False, autoLevels=False, autoHistogramRange=False)
        self.gui.toolBar.setFPS(fps)
        
    def start(self):
        self.gui = GUI_TOFcam635()
        self.gui.show()
        self.tof = TofCam635()
        self.tof.start()
        self.tof.set_fps_callback(self.gui.update_fps)
        self.tof.set_frame_callback(self.gui.update_frame)
        self.tof.set_chip_info_callback(self.gui.update_chip_info)


if __name__ == "__main__":
    cam = TofCam635(port='/dev/ttyACM0')
    app = QApplication([])
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam635()
    bridge = TofCam635Bridge(gui, cam)
    gui.show()
    app.exec_()