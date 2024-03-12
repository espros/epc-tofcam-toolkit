
import sys
import getopt
import numpy as np
import qdarktheme
from PySide6.QtWidgets import QApplication
from epc.tofCam611.camera import Camera as TOFcam611
from epc.tofCam611.serialInterface import SerialInterface
from epc.tofCam_gui import GUI_TOFcam611
from epc.tofCam_gui.streamer import Streamer, pause_streaming

class TOFcam611_bridge:
    C = 299792458 # m/s
    MAX_AMPLITUDE = 2800
    def __init__(self, gui: GUI_TOFcam611, cam: TOFcam611):
        self.gui = gui
        self.cam = cam
        self.__get_image_cb = cam.getDistance
        self.__distance_unambiguity = 7.5 # m 
        self.streamer = Streamer(self.get_image)
        self.streamer.signal_new_frame.connect(self.gui.updateImage)
        
        # update chip information
        chipID, waferId = cam.getChipInfo()
        gui.toolBar.setChipInfo(chipID, waferId)
        fw_version = cam.getFwRelease()
        gui.toolBar.setVersionInfo(f"{fw_version[0]}.{fw_version[1]}")

        # connect signals
        gui.topMenuBar.openConsoleAction.triggered.connect(lambda: gui.console.startup_kernel(cam))
        gui.toolBar.captureButton.triggered.connect(self.capture)
        gui.toolBar.playButton.triggered.connect(self._set_streaming)
        gui.imageTypeWidget.signal_value_changed.connect(self._set_image_type)
        gui.modulationFrequency.signal_value_changed.connect(lambda freq: self._set_modulation_settings())
        gui.integrationTimes.signal_value_changed.connect(self._set_integration_times)
        gui.minAmplitude.signal_value_changed.connect(lambda minAmp: self.cam.setMinAmplitude(minAmp))
        gui.temporalFilter.signal_filter_changed.connect(lambda: self.__set_filter_settings())

        self.gui.setDefaultValues()

        self.gui.imageView.pc.set_max_depth(int(self.__distance_unambiguity))

    def _set_streaming(self, enable: bool):
        if enable:
            self.streamer.start_stream()
        else:
            self.streamer.stop_stream()

    @pause_streaming
    def __set_filter_settings(self):
        temp_factor = 0.0
        temp_threshold = 0

        tempOn = self.gui.builtInFilter.temporalFilter.isChecked()
        if tempOn:
            temp_factor = self.gui.builtInFilter.temporalFilter.factor.value()
            temp_threshold = self.gui.builtInFilter.temporalFilter.threshold.value()
              
        self.cam.setFilter(temp_threshold, int(temp_factor*1000))

    @pause_streaming
    def _set_integration_times(self, type: str, value: int):
        tof = self.gui.integrationTimes.getTimeAtIndex(0)
        self.cam.setIntTime_us(tof)
        self.capture()

    @pause_streaming
    def _set_modulation_settings(self):
        frequency = float(self.gui.modulationFrequency.getSelection().split(' ')[0])
        self.__distance_unambiguity = self.C / (2 * frequency * 1e6)
        if(frequency == 20.0):
            freqIndex = 1
        else:
            freqIndex = 0 # for 10MHz

        self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        self.gui.imageView.pc.set_max_depth(int(self.__distance_unambiguity))
        self.cam.setModFrequency(freqIndex)
        self.capture()

    @pause_streaming
    def _set_image_type(self, image_type: str):
        if image_type == 'Distance':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.getDistance
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.__distance_unambiguity*1000)
        elif image_type == 'Amplitude':
            self.gui.imageView.setActiveView('image')
            self.__get_image_cb = self.cam.getAmplitude
            self.gui.imageView.setColorMap(self.gui.imageView.DISTANCE_CMAP)
            self.gui.imageView.setLevels(0, self.MAX_AMPLITUDE)
        elif image_type == 'Point Cloud':
            self.gui.imageView.setActiveView('pointcloud')
            self.__get_image_cb = self.cam.getPointCloud
        
        if not self.streamer.is_streaming():
            self.capture()

    def get_image(self):
         return self.__get_image_cb()
    
    def capture(self, mode=0):
        image = self.get_image()
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
    comPort = get_port()
    com = SerialInterface(comPort) 
    cam = TOFcam611(com)
    cam.powerOn()

    app = QApplication([])
    qdarktheme.setup_theme('auto', default_theme='dark')
    gui = GUI_TOFcam611()
    bridge = TOFcam611_bridge(gui, cam)
    gui.show()
    app.exec()

if __name__ == '__main__':
    main()