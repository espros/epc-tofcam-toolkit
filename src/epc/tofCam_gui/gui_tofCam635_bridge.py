import sys
import getopt
import qdarktheme
from PySide6.QtWidgets import QApplication
from epc.tofCam635 import TofCam635
from epc.tofCam_gui import GUI_TOFcam635
from epc.tofCam_gui.streamer import Streamer, pause_streaming
from epc.tofCam_lib.filters import gradimg, threshgrad, cannyE

class TofCam635Bridge:
    DEFAULT_INT_TIME_GRAY = 100
    DEFAULT_INT_TIME_DIST = 1000
    MAX_DISTANCE = 15000
    MAX_AMPLITUDE = 2896
    MAX_GRAYSCALE = 0xFF

    def __init__(self, gui: GUI_TOFcam635, cam: TofCam635) -> None:
        self.gui = gui
        self.cam = cam
        self.__get_image_cb = self.cam.get_distance_image
        self.streamer = Streamer(self.getImage)
        self.streamer.signal_new_frame.connect(self.gui.updateImage)
        self.captureMode = 0

        cam.cmd.setOperationMode(0)

        gui.toolBar.playButton.triggered.connect(lambda: self._set_streaming(gui.toolBar.playButton.isChecked()))
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.guiFilterGroupBox.selection_changed_signal.connect(self._setGuiFilter)
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

        self.gui.toolBar.setChipInfo(*self.cam.cmd.getChipInfo())
        self.gui.toolBar.setVersionInfo(self.cam.cmd.getFwRelease())
        self._changeImageType(gui.imageTypeWidget.comboBox.currentText())

    def getImage(self):
        return self.__get_image_cb(self.captureMode)

    def _setGuiFilter(self, filter: str):
        match filter:
            case 'None':
                self.gui.setFilter_cb(None)
            case 'Gradient':
                self.gui.setFilter_cb(gradimg)
            case 'Canny':
                self.gui.setFilter_cb(cannyE)
            case 'Threshold':
                self.gui.setFilter_cb(threshgrad)

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

    def _set_hdrTimesEnabled(self, enabled: bool):
        self.gui.integrationTimes.setTimeEnabled(1, enabled)
        self.gui.integrationTimes.setTimeEnabled(2, enabled)
        self.gui.integrationTimes.setTimeEnabled(3, enabled)
        self.gui.integrationTimes.autoMode.setEnabled(not enabled)

    @pause_streaming
    def __set_roi(self, x: int, y: int, w: int, h: int):
        self.cam.set_roi(x, y, w, h)

    @pause_streaming
    def _set_hdr_mode(self, mode: str):
        if mode == 'HDR Spatial':
            self._set_hdrTimesEnabled(False)
            self.cam.cmd.setHDR('spatial')
        elif mode == 'HDR Temporal':
            self._set_hdrTimesEnabled(True)
            self.gui.integrationTimes.set_hdr_mode()
            self.cam.cmd.setHDR('temporal')
        elif mode == 'HDR Off':
            self._set_hdrTimesEnabled(False)
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

    @pause_streaming
    def _changeImageType(self, imgType: str):
        self.imageType = imgType
        if imgType == 'Distance':
            self.__get_image_cb = self.cam.get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_DISTANCE)
        elif imgType == 'Amplitude':
            self.__get_image_cb = self.cam.get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif imgType == 'Grayscale':
            self.__get_image_cb = self.cam.get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        else:
            raise ValueError(f"Image Type '{imgType}' not supported")
        self.capture()


    def capture(self, mode=0):
        image = self.__get_image_cb(self.captureMode)
        self.gui.updateImage(image)

def get_port():
    port = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:", ['port='])
        for opt, arg in opts:
            if opt in ('-p', '--port'):
                port = arg
    except:
        print('Argument parsing failed')
    if port == None:
        print(f'No port specified. Trying to find port automatically')
    return port

def main():
    port = get_port()
    cam = TofCam635(port)

    app = QApplication([])
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam635()
    gui.centralWidget().releaseKeyboard()
    bridge = TofCam635Bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == "__main__":
    main()