from epc.tofCam635 import TofCam635
from epc.tofCam_gui.gui_tofCam635 import GUI_TOFcam635
from epc.tofCam_gui.settings_widget import IntegrationTimes, IntegrationTimes635

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
# from PyQt6.QtWidgets import QApplication
# from PyQt6.QtCore import QTimer
import qdarktheme
import time
import threading
import queue

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

        cam.cmd.setOperationMode(0)

        self.time_last_frame = time.time()
        self.gui.toolBar.playButton.triggered.connect(lambda: self._set_streaming(self.gui.toolBar.playButton.isChecked()))
        self.gui.integrationTimes.signal_value_changed.connect(self._update_int_time)
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.imageTypeWidget.selection_changed_signal.connect(self._changeImageType)
        gui.hdrModeDropDown.signal_selection_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(lambda value: self._set_min_amplitudes(value))

        gui.builtInFilter.medianFilter.signal_filter_changed.connect(lambda enable: self.cam.cmd.setMedianFilter(enable))
        gui.builtInFilter.temporalFilter.signal_filter_changed.connect(lambda enable, threshold, factor: self.cam.cmd.setTemporalFilter(enable, threshold, factor))
        gui.builtInFilter.averageFilter.signal_filter_changed.connect(lambda enable: self.cam.cmd.setAverageFilter(enable))
        gui.builtInFilter.edgeFilter.signal_filter_changed.connect(lambda enable, threshold: self.cam.cmd.setEdgeFilter(enable, threshold))
        gui.roiSettings.signal_roi_changed.connect(self.__set_roi)
        gui.modulationChannel.signal_selection_changed.connect(lambda channel: self.cam.cmd.setModChannel(int(channel)))

        self.updateChipID()
        self._changeImageType(gui.imageTypeWidget.comboBox.currentText())

        self.__is_streaming = False
        self.__streaming_thread = None

    def __set_roi(self, x: int, y: int, w: int, h: int):
        if self.__is_streaming:
            self.stopStreaming()
            self.cam.set_roi(x, y, w, h)
            self.startStreaming()
        else:
            self.cam.set_roi(x, y, w, h)


    def __streaming_thread_cb(self):
        self.__is_streaming = True
        while self.__is_streaming:
            self.capture(mode=1)

    def startStreaming(self):
        if self.__is_streaming:
            raise Exception("Already streaming")
        self.__streaming_thread = threading.Thread(target=self.__streaming_thread_cb, )
        self.__streaming_thread.start()

    def stopStreaming(self):
        if not self.__is_streaming:
            return
        self.__is_streaming = False
        self.__streaming_thread.join()
        self.cam.cmd.com.serial.flush()

    def _set_streaming(self, enable: bool):
        if enable:
            self.startStreaming()
        else:
            self.stopStreaming()

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
                self.gui.integrationTimes.set_auto_mode()
            else:
                self.cam.cmd.setIntTimeDist(0, self.gui.integrationTimes.wFOV[0].value())
                self.gui.integrationTimes.set_normal_mode()
        else:
            raise ValueError(f"Integration Time Type '{type}' not supported")

    def __get_grayscale_image(self, mode=0):
        return self.cam.get_grayscale_image(mode)

    def __get_distance_image(self, mode=0):
        return self.cam.get_distance_image(mode)

    def __get_amplitude_image(self, mode=0):
        return self.cam.get_amplitude_image(mode)

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

    def capture(self, mode=0):
        fps = round(1 / (time.time() - self.time_last_frame))
        self.time_last_frame = time.time()

        image = self.getImage_cb(mode)
        self.gui.imageView.setImage(image, autoRange=False, autoLevels=False, autoHistogramRange=False)
        self.gui.toolBar.setFPS(fps)

def main():
    app = QApplication([])
    cam = TofCam635(port='/dev/ttyACM0')
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam635()
    gui.centralWidget().releaseKeyboard()
    bridge = TofCam635Bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == "__main__":
    main()