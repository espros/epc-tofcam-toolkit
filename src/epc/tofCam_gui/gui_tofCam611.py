import sys
import qdarktheme
from PySide6 import QtWidgets  
from epc.tofCam_gui.widgets import VideoWidget, GroupBoxSelection, DropDownSetting, SettingsGroup, IntegrationTimes
from epc.tofCam_gui.widgets.filter_widgets import TemporalFilter
from epc.tofCam_gui import Base_GUI_TOFcam


class GUI_TOFcam611(Base_GUI_TOFcam):
    def __init__(self, title='TOF CAM 611 VIDEO STREAM', parent=None):
        super(GUI_TOFcam611, self).__init__(title)

        # Create the video widget
        self.imageView = VideoWidget()
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude'])
        self.integrationTimes = IntegrationTimes(['TOF'], defaults=[1000], limits=[1600])
        self.integrationTimes.autoMode.setVisible(False)
        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['20 MHz'])       
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency])
        
        self.temporalFilter = TemporalFilter()
        self.builtInFilter = SettingsGroup('Built-In Filters', [self.temporalFilter])

        #Create Layout for settings
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.builtInFilter)

        self.complete_setup()


def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam611()
    stream.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()