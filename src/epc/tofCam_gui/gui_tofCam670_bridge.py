
import getopt
import sys

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from epc.tofCam670.tofCam670 import TOFcam670, AcquisitionMode
from epc.tofCam_gui import Base_TOFcam_Bridge, GUI_TOFcam670
from epc.tofCam_gui.streamer import pause_streaming


class TOFcam670_bridge(Base_TOFcam_Bridge):
    C = 299792458 # m/s
    MAX_AMPLITUDE = 2800
    MAX_GRAYSCALE = 2**10
    MIN_DCS = 0
    MAX_DCS = 4096
    def __init__(self, gui: GUI_TOFcam670, cam: TOFcam670):
        super(TOFcam670_bridge, self).__init__(cam, gui)
        self._distance_unambiguity = 6.25 # m 
        self.cam: TOFcam670

        self.streamer.start_stream_cb = lambda: cam.cam.startStream()
        self.streamer.post_stop_cb = lambda: cam.cam.stopStream()

        # connect signals
        gui.imageTypeWidget.signal_value_changed.connect(self._set_image_type)
        gui.modulationFrequency.signal_value_changed.connect(lambda value: self._set_modulation_settings(value))
        gui.integrationTimes.signal_value_changed.connect(self._set_integration_times)
        gui.hdrModeDropDown.signal_value_changed.connect(self._set_hdr_mode)
        gui.minAmplitude.signal_value_changed.connect(self._set_min_amplitudes)
        gui.medianFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.averageFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.temporalFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.kalmanFilter.signal_filter_changed.connect(lambda: self._set_filter_settings())
        gui.lensType.signal_value_changed.connect(lambda value: self.cam.settings.set_lense_type(value))

        gui.setDefaultValues()
        gui.hdrModeDropDown.setEnabled(False)

    def getImage(self):
        if self.image_type == 'Point Cloud':
            return self._get_image_cb()
        else:
            image = self._get_image_cb()
            return np.rot90(image, 3)

    def storeImage(self, image):
        # Restore the rotation before storage
        if self.image_type == 'Point Cloud':
            pass
        else:
            image = np.rot90(image, 1)

        super().storeImage(image)

    def _set_filter_settings(self):
        if not isinstance(self.cam, TOFcam670):
            return
        self.cam.medianFilterOn = self.gui.medianFilter.isChecked()
        self.cam.averageFilterOn = self.gui.averageFilter.isChecked()
        self.cam.temporalFilterOn = self.gui.temporalFilter.isChecked()
        self.cam.temporalFilter.alpha = self.gui.temporalFilter.factor.value()
        self.cam.temporalFilter.threshold = self.gui.temporalFilter.threshold.value()
        self.cam.kalmanFilterOn = self.gui.kalmanFilter.isChecked()
        self.cam.kalmanFilter.uncertainty_threshold = self.gui.kalmanFilter.slider.value()

    def __set_hdrTimesEnabled(self, enabled: bool):
        self.gui.integrationTimes.setTimeEnabled(1, enabled)
        self.gui.integrationTimes.setTimeEnabled(2, enabled)

    @pause_streaming
    def _set_hdr_mode(self, mode: str):
        self._set_image_type(self.image_type)

    @pause_streaming
    def _set_roi(self, x1, y1, x2, y2):
        self.cam.settings.set_roi((x1, y1, x2, y2))

    def _set_min_amplitudes(self, minAmp: int):
        self.cam.settings.set_minimal_amplitude(minAmp)
        self.capture()

    def _set_integration_times(self, type="", value=0):
        if self.gui.hdrModeDropDown.getSelection() == 'HDR Temporal':
            low = self.gui.integrationTimes.getTimeAtIndex(0)
            mid = self.gui.integrationTimes.getTimeAtIndex(1)
            high = self.gui.integrationTimes.getTimeAtIndex(2)
            self.cam.settings.set_integration_hdr([low, mid, high])
            
            gray = self.gui.integrationTimes.getTimeAtIndex(3)
            self.cam.settings.set_integration_time_grayscale(gray)
        elif self.image_type == 'Grayscale':
            gray = self.gui.integrationTimes.getTimeAtIndex(3)
            self.cam.settings.set_integration_time_grayscale(gray)
        else:
            low = self.gui.integrationTimes.getTimeAtIndex(0)
            self.cam.settings.set_integration_time(low)
        self.capture()

    @pause_streaming
    def _set_flex_mod_freq(self, frequency: float):

        self.cam.settings.set_flex_mod_freq(frequency)
        self.capture()

    @pause_streaming
    def _set_modulation_settings(self, frequency=10):
        print(f"Setting modulation frequency to {frequency} MHz")
        if self.gui.imageTypeWidget.getSelection() == 'Distance':
            self._distance_unambiguity = self.C / (2 * frequency * 1e6)
            histogram = self.gui.imageView.getHistogramWidget()
            histogram.setHistogramRange(0, self._distance_unambiguity*1000*self.unit_scaling_factor)
        self.cam.settings.set_modulation(frequency)
        self.capture()

    def _set_standard_image_type(self, image_type):
        super(TOFcam670_bridge, self)._set_standard_image_type(image_type)
        histogram = self.gui.imageView.getHistogramWidget()
        if image_type in ['Distance', 'Point Cloud']:
            self.gui.imageView.setLevels(200*self.unit_scaling_factor, 2500*self.unit_scaling_factor)  # override default levels
            histogram.setHistogramRange(0, self._distance_unambiguity*1000*self.unit_scaling_factor)
        elif image_type == 'DCS':
            self.gui.imageView.setLevels(self.MIN_DCS, self.MAX_DCS)  # override default levels
            histogram.setHistogramRange(self.MIN_DCS, self.MAX_DCS)
        else:
            levels = self.gui.imageView.video.getLevels()
            histogram.setHistogramRange(*levels)

    @pause_streaming
    def _set_image_type(self, image_type: str):
        self.image_type = image_type
        self.gui.pointCloudSettings.setEnabled(image_type == 'Point Cloud')

        self._set_standard_image_type(image_type)
        
        if image_type in ['Distance', 'Amplitude', 'Point Cloud']:
            if self.gui.hdrModeDropDown.getSelection() == 'HDR Temporal':
                self.cam.settings.set_acquisition_mode(AcquisitionMode.DIST_AMP_HDR)
                self.cam.settings.set_hdr(2)
                self.__set_hdrTimesEnabled(True)
            else:
                self.cam.settings.set_acquisition_mode(AcquisitionMode.DIST_AMP)
                self.cam.settings.set_hdr(0)
                self.__set_hdrTimesEnabled(False)
            self._set_min_amplitudes(self.gui.minAmplitude.slider.value())
        elif image_type == 'DCS':
            self.cam.settings.set_acquisition_mode(AcquisitionMode.DCS4)
        elif image_type == 'Grayscale':
            self.cam.settings.set_acquisition_mode(AcquisitionMode.GRAYSCALE)

        self._set_integration_times()
        self._set_modulation_settings(self.gui.modulationFrequency.spinBox.value())
        if not self.streamer.is_streaming():
            self.capture()

def main():
    app = QApplication([])
    #qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam670()
    
    # ip_address = get_ipAddress()
    cam = TOFcam670()
    cam.initialize()

    bridge = TOFcam670_bridge(gui, cam)

    longopts = ["fullscreen", "maximized", "start-stream"]
    opts, args = getopt.getopt(sys.argv[1:], "", longopts)
    opts = dict(opts)

    if "--fullscreen" in opts:
        gui.showFullScreen()
    elif "--maximized" in opts:
        gui.showMaximized()
    else:
        gui.show()

    if "--start-stream" in opts:
        QTimer.singleShot(100, gui.toolBar.playButton.trigger)
        
    app.exec()

if __name__ == '__main__':
    main()
