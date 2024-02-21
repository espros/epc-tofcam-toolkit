from epc.tofCam635 import TofCam635
from epc.tofCam_gui.gui_tofCam635 import GUI_TOFcam635
from epc.tofCam_gui.streamer import Streamer, pause_streaming

from PySide6.QtWidgets import QApplication
import qdarktheme

class TofCam635Bridge:
    DEFAULT_INT_TIME_GRAY = 100
    DEFAULT_INT_TIME_DIST = 1000
    MAX_DISTANCE = 15000
    MAX_AMPLITUDE = 2896
    MAX_GRAYSCALE = 0xFF

    def __init__(self, gui: GUI_TOFcam635, cam: TofCam635) -> None:
        self.gui = gui
        self.cam = cam
        self.__get_image_cb = self.__get_distance_image
        self.streamer = Streamer(self.__get_image_cb)
        self.streamer.signal_new_frame.connect(self.gui.updateImage)
        self.captureMode = 0

        cam.cmd.setOperationMode(0)

        gui.toolBar.playButton.triggered.connect(lambda: self._set_streaming(gui.toolBar.playButton.isChecked()))
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.integrationTimes.signal_value_changed.connect(self._update_int_time)
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

    @pause_streaming
    def __set_roi(self, x: int, y: int, w: int, h: int):
        self.cam.set_roi(x, y, w, h)

    def _set_streaming(self, enable: bool):
        if enable:
            self.captureMode = 1
            self.streamer.start_stream()
        else:
            self.captureMode = 0
            self.streamer.stop_stream()

    def _set_min_amplitudes(self, minAmp: int):
        for i in range(5):
            self.cam.cmd.setAmplitudeLimit(i, minAmp)

    @pause_streaming
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

    @pause_streaming
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

    @pause_streaming
    def _changeImageType(self, imgType: str):
        self.imageType = imgType
        if imgType == 'Distance':
            self.__get_image_cb = self.__get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_DISTANCE)
        elif imgType == 'Amplitude':
            self.__get_image_cb = self.__get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif imgType == 'Grayscale':
            self.__get_image_cb = self.__get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        else:
            raise ValueError(f"Image Type '{imgType}' not supported")
        self.capture()

    def updateChipID(self):
        self.gui.toolBar.setChipInfo(*self.cam.cmd.getChipInfo())

    def capture(self, mode=0):
        image = self.__get_image_cb(self.captureMode)
        self.gui.updateImage(image)

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