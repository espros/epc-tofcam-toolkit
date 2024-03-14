import sys
import qdarktheme
from PySide6 import QtWidgets
from epc.tofCam_gui import Base_GUI_TOFcam
from epc.tofCam_gui.widgets import VideoWidget, IntegrationTimes, GroupBoxSelection, DropDownSetting, SettingsGroup, SpinBoxSetting, RoiSettings
from epc.tofCam_gui.widgets.filter_widgets import SimpleFilter, TemporalFilter, EdgeFilter, InterferenceFilter

class GUI_TOFcam635(Base_GUI_TOFcam):
    def __init__(self, title='GUI-TOFcam635', parent=None):
        super(GUI_TOFcam635, self).__init__(title)

        # Create Widgets
        self.imageView = VideoWidget()
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale', 'Point Cloud'])
        self.guiFilterGroupBox = GroupBoxSelection('GUI Filters', ['None', 'Canny', 'Gradient', 'Threshold'])
        self.hdrModeDropDown = DropDownSetting('HDR Mode', ['HDR Off'])
        self.modulationChannel = DropDownSetting('Modulation Channel', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15'])
        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['20 MHz'])
        self.operationMode = DropDownSetting('Operation Mode', ['WFO'])
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency, self.modulationChannel, self.operationMode, self.hdrModeDropDown])
        self.integrationTimes = IntegrationTimes(['Integration Time 1', 'Gray'], [125, 50], [1000, 50000])
        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000, default=100)
        
        self.medianFilter = SimpleFilter('Median Filter')
        self.averageFilter = SimpleFilter('Average Filter')
        self.edgeFilter = EdgeFilter(threshold=150)
        self.temporalFilter = TemporalFilter(threshold=150, factor=0.1)
        self.interferenceFilter = InterferenceFilter(limit=500, useLast_on=True)
        self.builtInFilter = SettingsGroup('Built-In Filters', [self.medianFilter, self.averageFilter, self.edgeFilter, self.temporalFilter, self.interferenceFilter])

        self.roiSettings = RoiSettings(160, 60, steps=4)

        # Create Layout for settings
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.guiFilterGroupBox)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)
        self.settingsLayout.addWidget(self.roiSettings)

        self.complete_setup()
        
def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam635()
    stream.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()