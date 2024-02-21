import numpy as np
import qdarktheme
from PySide6.QtWidgets import QApplication
from epc.tofCam660.server import Server as TOFcam660
from epc.tofCam_gui.gui_tofCam660 import GUI_TOFcam660
from epc.tofCam660.productfactory import ProductFactory
from epc.tofCam_gui.streamer import Streamer, pause_streaming

class TOFcam660_bridge:
    C = 299792458 # m/s
    MAX_AMPLITUDE = 2800
    MAX_GRAYSCALE = 2**10
    def __init__(self, gui: GUI_TOFcam660, cam: TOFcam660):
        self.gui = gui
        self.cam = cam
        self.__get_image_cb = cam.getTofDistance
        self.__distance_resolution = 0.01 # mm/bit
        self.__distance_unambiguity = 6.25 # m 
        self.streamer = Streamer(self.getImage)
        self.streamer.signal_new_frame.connect(self.gui.updateImage)
        
        # update chip information
        chipID = cam.getChipId()
        waferId = cam.getWaferId()
        gui.toolBar.setChipInfo(chipID, waferId)

        # connect signals
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.toolBar.playButton.triggered.connect(self._set_streaming)
        gui.imageTypeWidget.selection_changed_signal.connect(self._set_image_type)
        gui.modulationFrequency.signal_selection_changed.connect(lambda freq: self._set_modulation_settings())
        gui.modulationChannel.signal_selection_changed.connect(lambda: self._set_modulation_settings())
        gui.integrationTimes.signal_value_changed.connect(self._set_integration_times)
        gui.hdrModeDropDown.signal_selection_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(lambda value: self.cam.setMinAmplitude(value))
        gui.builtInFilter.medianFilter.signal_filter_changed.connect(self.__set_filter_settings)
        gui.builtInFilter.temporalFilter.signal_filter_changed.connect(self.__set_filter_settings)
        gui.builtInFilter.averageFilter.signal_filter_changed.connect(self.__set_filter_settings)
        gui.builtInFilter.edgeFilter.signal_filter_changed.connect(self.__set_filter_settings)
        gui.builtInFilter.interferenceFilter.signal_filter_changed.connect(self.__set_filter_settings)
        gui.roiSettings.signal_roi_changed.connect(lambda x1, y1, x2, y2: self.cam.setRoi(x1, y1, x2, y2))

        # set default settings
        self.__set_hdrTimesEnabled(False)
        self._set_image_type('Distance')
        self._set_modulation_settings()
        self._set_integration_times('Low', 100)


    def getImage(self):
        image = self.__get_image_cb()
        return np.rot90(image, 1, (2, 1))

    def _set_streaming(self, enable: bool):
        if enable:
            self.streamer.start_stream()
        else:
            self.streamer.stop_stream()

    def __set_filter_settings(self):
        temp_factor = 0
        temp_threshold = 0
        edgeThreshold = 0
        interferenceLimit = 0
        interferenceUseLatest = False

        tempOn = self.gui.builtInFilter.temporalFilter.isChecked()
        medianOn = self.gui.builtInFilter.medianFilter.isChecked()
        averageOn = self.gui.builtInFilter.averageFilter.isChecked()
        edgeOn = self.gui.builtInFilter.edgeFilter.isChecked()
        interferenceOn = self.gui.builtInFilter.interferenceFilter.isChecked()

        if tempOn:
            temp_factor = self.gui.builtInFilter.temporalFilter.factor.value()
            temp_threshold = self.gui.builtInFilter.temporalFilter.threshold.value()
        if edgeOn:
            edgeThreshold = self.gui.builtInFilter.edgeFilter.threshold.value()
        if interferenceOn:
            interferenceLimit = self.gui.builtInFilter.interferenceFilter.limit.value()
            interferenceUseLatest = self.gui.builtInFilter.interferenceFilter.useLastValue.isChecked()     

        self.cam.setFilter(medianOn, averageOn, edgeThreshold, temp_factor, temp_threshold, interferenceLimit, interferenceUseLatest)

    def __set_hdrTimesEnabled(self, enabled: bool):
        self.gui.integrationTimes.setEnabled(1, enabled)
        self.gui.integrationTimes.setEnabled(2, enabled)

    @pause_streaming
    def _set_hdr_mode(self, mode: str):
        if mode == 'HDR Off':
            self.cam.setHdr(0)
            self.__set_hdrTimesEnabled(False)
        elif mode == 'HDR Spatial':
            self.cam.setHdr(1)
            self.__set_hdrTimesEnabled(False)
        elif mode == 'HDR Temporal':
            self.cam.setHdr(2)
            self.__set_hdrTimesEnabled(True)

    @pause_streaming
    def _set_integration_times(self, type: str, value: int):
        low = self.gui.integrationTimes.getTimeAtIndex(0)
        mid = self.gui.integrationTimes.getTimeAtIndex(1)
        high = self.gui.integrationTimes.getTimeAtIndex(2)
        gray = self.gui.integrationTimes.getTimeAtIndex(3)
        self.cam.setIntTimesus(gray, low, mid, high)
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
        self.cam.setModulationFrequencyMHz(frequency, channel)
        self.capture()

    @pause_streaming
    def _set_image_type(self, image_type: str):
        if image_type == 'Distance':
            self.__get_image_cb = self.cam.getTofDistance
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        elif image_type == 'Amplitude':
            self.__get_image_cb = self.cam.getTofAmplitude
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif image_type == 'Grayscale':
            self.__get_image_cb = self.cam.getGrayscaleAmplitude
            self.gui.imageView.setColorMap(self.gui.imageView.GRAYSCALE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_GRAYSCALE)
        
        if not self.streamer.is_streaming():
            self.capture()

    def capture(self, mode=0):
        image = self.getImage()
        self.gui.updateImage(image)

def main():
    app = QApplication([])
    cam = TOFcam660()
    cam.setProduct(ProductFactory().create_product('660_ethernet', 0))
    cam.startup()
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam660()
    bridge = TOFcam660_bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == '__main__':
    main()