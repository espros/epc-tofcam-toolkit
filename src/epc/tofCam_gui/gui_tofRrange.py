import sys
import qdarktheme
from PySide6 import QtWidgets  
from epc.tofCam_gui.widgets import VideoWidget, GroupBoxSelection, DropDownSetting, SettingsGroup, IntegrationTimes, SpinBoxSetting
from epc.tofCam_gui.widgets.filter_widgets import TemporalFilter
from epc.tofCam_gui import Base_GUI_TOFcam


class GUI_TOFrange611(Base_GUI_TOFcam):
    def __init__(self, title='TOF RANGE 611 VIDEO STREAM', parent=None):
        super(GUI_TOFrange611, self).__init__(title)

        # Create the video widget
        self.imageView = VideoWidget()
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Point Cloud'])
        self.integrationTimes = IntegrationTimes(['TOF'], defaults=[100], limits=[1600])
        self.integrationTimes.autoMode.setVisible(False)
        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000, default=50)
        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['10 MHz','20 MHz'])       
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency])
        
        self.temporalFilter = TemporalFilter(threshold=40, factor=0.1)
        self.builtInFilter = SettingsGroup('Built-In Filters', [self.temporalFilter])

        #Create Layout for settings
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)

        self.complete_setup()


def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFrange611()
    stream.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()