
import sys
import getopt
import numpy as np
import qdarktheme
from PySide6.QtWidgets import QApplication
from epc.tofCam660.epc660 import Epc660Ethernet
# from epc.tofCam660.server import Server as TOFcam660
from epc.tofCam660.tofCam660 import TOFcam660
from epc.tofCam_gui import GUI_TOFcam660
from epc.tofCam_gui.streamer import Streamer, pause_streaming
from epc.tofCam_lib.filters import gradimg, threshgrad, cannyE

class TOFcam660_bridge:
    C = 299792458 # m/s
    MAX_AMPLITUDE = 2800
    MAX_GRAYSCALE = 2**10
    def __init__(self, gui: GUI_TOFcam660, cam: TOFcam660):
        self.gui = gui
        self.cam = cam
        self.__get_image_cb = cam.get_distance_image
        self.image_type = 'Distance'
        self.__distance_resolution = 0.01 # mm/bit
        self.__distance_unambiguity = 6.25 # m 
        self.streamer = Streamer(self.getImage)
        self.streamer.signal_new_frame.connect(self.gui.updateImage)
        
        # update chip information
        chipID, waferId = cam.device.get_chip_infos()
        gui.toolBar.setChipInfo(chipID, waferId)
        fw_version = cam.device.get_fw_version()
        gui.toolBar.setVersionInfo(fw_version)

        # connect signals
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.toolBar.playButton.triggered.connect(self._set_streaming)
        gui.topMenuBar.openConsoleAction.triggered.connect(lambda: gui.console.startup_kernel(cam))
        gui.imageTypeWidget.signal_value_changed.connect(self._set_image_type)
        gui.guiFilterGroupBox.signal_value_changed.connect(self._setGuiFilter)
        gui.modulationFrequency.signal_value_changed.connect(lambda: self._set_modulation_settings())
        gui.modulationChannel.signal_value_changed.connect(lambda: self._set_modulation_settings())
        gui.integrationTimes.signal_value_changed.connect(self._set_integration_times)
        gui.hdrModeDropDown.signal_value_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(self._set_min_amplitudes)
        gui.medianFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.temporalFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.averageFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.edgeFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.interferenceFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.roiSettings.signal_roi_changed.connect(self._set_roi)
        gui.lensType.signal_value_changed.connect(lambda value: self.cam.settings.set_lense_type(value))

        gui.setDefaultValues()
        
        self.gui.imageView.pc.set_max_depth(int(self.__distance_unambiguity))

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

    def getImage(self):
        if self.image_type == 'Point Cloud':
            return self.__get_image_cb()
        else:
            image = self.__get_image_cb()
            return np.rot90(image, 3)

    def _set_streaming(self, enable: bool):
        if enable:
            self.streamer.start_stream()
        else:
            self.streamer.stop_stream()

    @pause_streaming
    def _set_filter_settings(self):
        temp_factor = 0.0
        temp_threshold = 0
        edgeThreshold = 0
        interferenceLimit = 0
        interferenceUseLatest = False

        tempOn = self.gui.temporalFilter.isChecked()
        medianOn = self.gui.medianFilter.isChecked()
        averageOn = self.gui.averageFilter.isChecked()
        edgeOn = self.gui.edgeFilter.isChecked()
        interferenceOn = self.gui.interferenceFilter.isChecked()

        if tempOn:
            temp_factor = self.gui.temporalFilter.factor.value()
            temp_threshold = self.gui.temporalFilter.threshold.value()
        if edgeOn:
            edgeThreshold = self.gui.edgeFilter.threshold.value()
        if interferenceOn:
            interferenceLimit = self.gui.interferenceFilter.limit.value()
            interferenceUseLatest = self.gui.interferenceFilter.useLastValue.isChecked()     

        self.cam.settings.set_filters(int(medianOn), int(averageOn), edgeThreshold, int(temp_factor*1000), temp_threshold, interferenceLimit, int(interferenceUseLatest))

    def __set_hdrTimesEnabled(self, enabled: bool):
        self.gui.integrationTimes.setTimeEnabled(1, enabled)
        self.gui.integrationTimes.setTimeEnabled(2, enabled)

    @pause_streaming
    def _set_hdr_mode(self, mode: str):
        if mode == 'HDR Off':
            self.cam.settings.set_hdr(0)
            self.__set_hdrTimesEnabled(False)
        elif mode == 'HDR Spatial':
            self.cam.settings.set_hdr(1)
            self.__set_hdrTimesEnabled(False)
        elif mode == 'HDR Temporal':
            self.cam.settings.set_hdr(2)
            self.__set_hdrTimesEnabled(True)

    @pause_streaming
    def _set_roi(self, x1, y1, x2, y2):
        self.cam.settings.set_roi((x1, y1, x2, y2))

    @pause_streaming
    def _set_min_amplitudes(self, minAmp: int):
        self.cam.settings.set_minimal_amplitude(minAmp)

    @pause_streaming
    def _set_integration_times(self, type: str, value: int):
        low = self.gui.integrationTimes.getTimeAtIndex(0)
        mid = self.gui.integrationTimes.getTimeAtIndex(1)
        high = self.gui.integrationTimes.getTimeAtIndex(2)
        gray = self.gui.integrationTimes.getTimeAtIndex(3)
        self.cam.settings.set_integration_hdr([gray, low, mid, high])
        self.capture()

    @pause_streaming
    def _set_modulation_settings(self):
        frequency = float(self.gui.modulationFrequency.getSelection().split(' ')[0])
        channel = int(self.gui.modulationChannel.getSelection())
        self.__distance_unambiguity = self.C / (2 * frequency * 1e6)
        if frequency >= 3:
            self.__distance_resolution = 0.01 # m/bit
        else:
            self.__distance_resolution = 0.1 # m/bit

        self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        self.gui.imageView.pc.set_max_depth(int(self.__distance_unambiguity))
        self.cam.settings.set_modulation(frequency, channel)
        self.capture()

    @pause_streaming
    def _set_image_type(self, image_type: str):
        self.image_type = image_type
        self.gui.pointCloudSettings.setEnabled(image_type == 'Point Cloud')
        self.gui.guiFilterGroupBox.setEnabled(image_type != 'Point Cloud')
        if image_type == 'Distance':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.get_distance_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        elif image_type == 'Amplitude':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.get_amplitude_image
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif image_type == 'Grayscale':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.get_grayscale_image
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        elif image_type == 'Point Cloud':
            self.gui.imageView.setActiveView('pointcloud')
            self.__get_image_cb = self.cam.get_point_cloud

        self._set_hdr_mode(self.gui.hdrModeDropDown.getSelection())
        
        if not self.streamer.is_streaming():
            self.capture()

    def capture(self, mode=0):
        image = self.getImage()
        self.gui.updateImage(image)

def get_ipAddress():
    ip_address = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:p:", ["ip=", 'port='])
        for opt, arg in opts:
            if opt in ('-i', '--ip'):
                ip_address = arg
            elif opt in ('-p', '--port'):
                port = arg
    except:
        print('Argument parsing failed')
    if ip_address == None:
        ip_address = '10.10.31.180'
        print(f'No ip-address specified. Trying to use default ip-address {ip_address}')
    return ip_address

def main():
    app = QApplication([])
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam660()
    
    ip_address = get_ipAddress()
    cam = TOFcam660(ip_address)
    cam.initialize()

    bridge = TOFcam660_bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == '__main__':
    main()