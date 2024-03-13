import sys
import getopt
import logging
import qdarktheme
from PySide6.QtWidgets import QApplication
from epc.tofCam635 import TofCam635
from epc.tofCam_gui import GUI_TOFcam635
from epc.tofCam_gui.streamer import Streamer, pause_streaming
from epc.tofCam_lib.filters import gradimg, threshgrad, cannyE

log = logging.getLogger('BRIDGE')

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
        self.__distance_unambiguity = 7.5 # m 

        cam.cmd.setOperationMode(0)

        gui.topMenuBar.openConsoleAction.triggered.connect(lambda: gui.console.startup_kernel(cam))
        gui.toolBar.playButton.triggered.connect(lambda: self._set_streaming(gui.toolBar.playButton.isChecked()))
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.guiFilterGroupBox.signal_value_changed.connect(self._setGuiFilter)
        gui.integrationTimes.signal_value_changed.connect(self._update_int_time)
        gui.imageTypeWidget.signal_value_changed.connect(self._changeImageType)
        gui.hdrModeDropDown.signal_value_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(lambda value: self._set_min_amplitudes(value))

        gui.medianFilter.signal_filter_changed.connect(lambda enable: self.cam.cmd.setMedianFilter(enable))
        gui.temporalFilter.signal_filter_changed.connect(lambda enable, threshold, factor: self.cam.cmd.setTemporalFilter(enable, int(threshold), int(1000*factor)))
        gui.averageFilter.signal_filter_changed.connect(lambda enable: self.cam.cmd.setAverageFilter(enable))
        gui.interferenceFilter.signal_filter_changed.connect(lambda enable, limit, useLast: self.cam.cmd.setInterferenceDetection(enable, useLast, limit))
        gui.edgeFilter.signal_filter_changed.connect(lambda enable, threshold: self.cam.cmd.setEdgeFilter(enable, threshold))
        gui.roiSettings.signal_roi_changed.connect(self.__set_roi)
        gui.modulationChannel.signal_value_changed.connect(lambda channel: self.cam.cmd.setModChannel(int(channel)))
        gui.modulationFrequency.signal_value_changed.connect(self._set_mod_freq)

        self.gui.toolBar.setChipInfo(*self.cam.cmd.getChipInfo())
        self.gui.toolBar.setVersionInfo(self.cam.cmd.getFwRelease())
        self.gui.setDefaultValues()

        self.gui.imageView.pc.set_max_depth(int(self.__distance_unambiguity))

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

    def _update_intTimes_enabled(self):
        hdr_mode = self.gui.hdrModeDropDown.getSelection()
        auto_int_en = self.gui.integrationTimes.autoMode.isChecked()
        if auto_int_en:
            self.gui.integrationTimes.setTimeEnabled(0, False)
            self.gui.integrationTimes.setTimeEnabled(1, False)
        elif hdr_mode == 'HDR Off':
            self.gui.integrationTimes.setTimeEnabled(0, True)
            self.gui.integrationTimes.setTimeEnabled(1, False)
        elif hdr_mode == 'HDR Temporal':
            self.gui.integrationTimes.setTimeEnabled(0, True)
            self.gui.integrationTimes.setTimeEnabled(1, True)
        else:
            raise ValueError(f"Undefined behavior for HDR Mode '{hdr_mode}'")

    @pause_streaming
    def __set_roi(self, x: int, y: int, w: int, h: int):
        self.cam.set_roi(x, y, w, h)

    def _set_mod_freq(self, freq: str):
        if freq == '10 MHz':
            self.cam.cmd.setModFrequency(0)
        elif freq == '20 MHz':
            self.cam.cmd.setModFrequency(1)
        else:
            raise ValueError(f"Modulation Frequency '{freq}' not supported")

    @pause_streaming
    def _set_hdr_mode(self, mode: str):
        if mode == 'HDR Spatial':
            self.cam.cmd.setHDR('spatial')
        elif mode == 'HDR Temporal':
            self.cam.cmd.setHDR('temporal')
        elif mode == 'HDR Off':
            self.cam.cmd.setHDR('off')
        else:
            raise ValueError(f"HDR Mode '{mode}' not supported")
        self._update_intTimes_enabled()

    @pause_streaming
    def _update_int_time(self, type: str, intTime: int):
        if   type == 'Integration Time 1':
            self.cam.cmd.setIntTimeDist(0, intTime)
        elif type == 'Integration Time 2':
            self.cam.cmd.setIntTimeDist(1, intTime)
        elif type == 'Gray':
            self.cam.cmd.setIntTimeGray(0, intTime)
        elif type == 'auto':
            if intTime == 1:
                self.cam.cmd.setIntTimeDist(0xFF, intTime)
            else:
                self.cam.cmd.setIntTimeDist(0, self.gui.integrationTimes.getTimeAtIndex(0))
            self._update_intTimes_enabled()
        else:
            raise ValueError(f"Integration Time Type '{type}' not supported")

    @pause_streaming
    def _changeImageType(self, imgType: str):
        self.gui.guiFilterGroupBox.setEnabled(imgType != 'Point Cloud')
        if imgType == 'Distance':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        elif imgType == 'Amplitude':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif imgType == 'Grayscale':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        elif imgType == 'Point Cloud':
            self.gui.imageView.setActiveView('pointcloud')
            self.__get_image_cb = self.cam.get_point_cloud
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
        log.error('Argument parsing failed')
    if port == None:
        log.info(f'No port specified. Trying to find port automatically')
    return port

def main():
    port = get_port()
    try:
        cam = TofCam635(port)
    except Exception as e:
        log.error(f'Failed to connect to device. Is the device running and connected?')
        return

    app = QApplication([])
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam635()
    gui.centralWidget().releaseKeyboard()
    bridge = TofCam635Bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == "__main__":
    main()