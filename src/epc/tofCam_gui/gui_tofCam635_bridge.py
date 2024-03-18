import sys
import getopt
import logging
import qdarktheme
import numpy as np
from PySide6.QtWidgets import QApplication
from epc.tofCam635.tofCam635 import TOFcam635
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

    def __init__(self, gui: GUI_TOFcam635, cam: TOFcam635) -> None:
        self.gui = gui
        self.cam = cam
        self.__get_image_cb = self.cam.get_distance_image
        self.streamer = Streamer(self.getImage, post_stop_cb=self.__stop_streaming_cb)
        self.streamer.signal_new_frame.connect(self.gui.updateImage)
        self.__distance_unambiguity = 7.5 # m 

        cam.settings.set_operation_mode(0)

        gui.topMenuBar.openConsoleAction.triggered.connect(lambda: gui.console.startup_kernel(cam))
        gui.toolBar.playButton.triggered.connect(lambda: self._set_streaming(gui.toolBar.playButton.isChecked()))
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.guiFilterGroupBox.signal_value_changed.connect(self._setGuiFilter)
        gui.integrationTimes.signal_value_changed.connect(self._update_int_time)
        gui.imageTypeWidget.signal_value_changed.connect(self._changeImageType)
        gui.hdrModeDropDown.signal_value_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(lambda value: self._set_min_amplitudes(value))

        gui.medianFilter.signal_filter_changed.connect(lambda enable: self.cam.settings.set_median_filter(enable))
        gui.temporalFilter.signal_filter_changed.connect(lambda enable, threshold, factor: self.cam.settings.set_temporal_filter(enable, int(threshold), int(1000*factor)))
        gui.averageFilter.signal_filter_changed.connect(lambda enable: self.cam.settings.set_average_filter(enable))
        gui.interferenceFilter.signal_filter_changed.connect(lambda enable, limit, useLast: self.cam.settings.set_interference_detection(enable, useLast, limit))
        gui.edgeFilter.signal_filter_changed.connect(lambda enable, threshold: self.cam.settings.set_edge_filter(enable, threshold))
        gui.roiSettings.signal_roi_changed.connect(self.__set_roi)
        gui.modulationChannel.signal_value_changed.connect(self._set_mod_freq)
        gui.modulationFrequency.signal_value_changed.connect(self._set_mod_freq)

        self.gui.toolBar.setChipInfo(*self.cam.device.get_chip_infos())
        self.gui.toolBar.setVersionInfo(self.cam.device.get_fw_version())
        self.gui.setDefaultValues()

        self.gui.imageView.pc.set_max_depth(int(self.__distance_unambiguity))

    def getImage(self):
        if self.gui.imageTypeWidget.getSelection() == 'Point Cloud':
            return self.__get_image_cb()
        else:
            image = self.__get_image_cb()
            return np.rot90(image, 3)
    
    def __stop_streaming_cb(self):
        self.cam.settings.set_capture_mode(0)
        self.getImage() # trow away image in pipeline

    @pause_streaming
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
            self.cam.settings.set_capture_mode(1)
            self.streamer.start_stream()
        else:
            self.streamer.stop_stream()
            self.cam.settings.set_capture_mode(0)

    @pause_streaming
    def _set_min_amplitudes(self, minAmp: int):
        self.cam.settings.set_minimal_amplitude(minAmp)

    def _update_intTimes_enabled(self):
        hdr_mode = self.gui.hdrModeDropDown.getSelection()
        auto_int_en = self.gui.integrationTimes.autoMode.isChecked()
        if auto_int_en:
            self.gui.integrationTimes.setTimeEnabled(0, False)
            self.gui.integrationTimes.setTimeEnabled(1, False)
        elif hdr_mode == 'HDR Off':
            self.gui.integrationTimes.setTimeEnabled(0, True)
            self.gui.integrationTimes.setTimeEnabled(1, True)
        elif hdr_mode == 'HDR Temporal':
            self.gui.integrationTimes.setTimeEnabled(0, True)
            self.gui.integrationTimes.setTimeEnabled(1, True)
        else:
            raise ValueError(f"Undefined behavior for HDR Mode '{hdr_mode}'")

    @pause_streaming
    def __set_roi(self, x1: int, y1: int, x2: int, y2: int):
        self.cam.settings.set_roi((x1, y1, x2, y2))
        try:
            self.getImage() # trow away next image since it has wrong roi
        except:
            pass

    @pause_streaming
    def _set_mod_freq(self, freq: str, channel=0):
        freq = self.gui.modulationFrequency.getSelection().split(' ')[0]
        channel = self.gui.modulationChannel.getSelection()
        self.cam.settings.set_modulation(float(freq), int(channel))

    @pause_streaming
    def _set_hdr_mode(self, mode: str):
        if mode == 'HDR Spatial':
            self.cam.settings.set_hdr('spatial')
        elif mode == 'HDR Temporal':
            self.cam.settings.set_hdr('temporal')
        elif mode == 'HDR Off':
            self.cam.settings.set_hdr('off')
        else:
            raise ValueError(f"HDR Mode '{mode}' not supported")
        self._update_intTimes_enabled()

    @pause_streaming
    def _update_int_time(self, type: str, intTime: int):
        if   type == 'Integration Time 1':
            self.cam.settings.set_integration_time_hdr(0, intTime)
        elif type == 'Integration Time 2':
            self.cam.settings.set_integration_time_hdr(1, intTime)
        elif type == 'Gray':
            self.cam.settings.set_integration_time_grayscale(intTime)
        elif type == 'auto':
            if intTime == 1:
                self.cam.settings.set_integration_time_hdr(0xFF, intTime)
            else:
                self.cam.settings.set_integration_time_hdr(0, self.gui.integrationTimes.getTimeAtIndex(0))
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
        image = self.getImage()
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
        cam = TOFcam635(port)
    except Exception as e:
        log.error(f'Failed to connect to device. Is the device running and connected?')
        return
    cam.initialize()

    app = QApplication([])
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam635()
    gui.centralWidget().releaseKeyboard()
    bridge = TofCam635Bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == "__main__":
    main()