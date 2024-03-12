import sys
import qdarktheme
from PySide6 import QtWidgets  
from epc.tofCam_gui.widgets import VideoWidget, GroupBoxSelection, DropDownSetting, SettingsGroup, SpinBoxSetting, RoiSettings, IntegrationTimes
from epc.tofCam_gui.widgets.filter_widgets import SimpleFilter, TemporalFilter, EdgeFilter, InterferenceFilter
from epc.tofCam_gui import Base_GUI_TOFcam

class ROISettings660(RoiSettings):
    def __init__(self, width, height):
        super(ROISettings660, self).__init__(width, height)

    def roiChanged(self):
        """ Overwrite the roiChanged method to update the y2 value when y1 is changed and vice versa """
        sender = self.sender()
        if sender == self.y1:
            self.y2.setValue(self.roi_height - self.y1.value())
        elif sender == self.y2:
            self.y1.setValue(self.roi_height - self.y2.value())
        super().roiChanged()


class GUI_TOFcam660(Base_GUI_TOFcam):
    def __init__(self, title='GUI-TOFcam660', parent=None):
        super(GUI_TOFcam660, self).__init__(title)

        # Create the video widget
        self.imageView = VideoWidget()
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale', 'Point Cloud'])
        self.guiFilterGroupBox = GroupBoxSelection('GUI Filters', ['None', 'Canny', 'Gradient'])
        self.hdrModeDropDown = DropDownSetting('HDR Mode', ['HDR Off', 'HDR Spatial', 'HDR Temporal'], default='HDR Temporal')
        self.modulationChannel = DropDownSetting('Modulation Channel', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15'])
        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['24 MHz', '12 MHz', '6 MHz', '3 MHz', '1.5 MHz', '0.75 MHz'], default='12 MHz')
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency, self.modulationChannel, self.hdrModeDropDown])
        self.lensType = DropDownSetting('Lens Type', ['Wide Field', 'Narrow Field', 'Standard Field'])
        self.pointCloudSettings = SettingsGroup('Point Cloud Settings', [self.lensType])
        self.pointCloudSettings.setEnabled(False)
        self.integrationTimes = IntegrationTimes(['Low', 'Mid', 'High', 'Grayscale'], [40, 400, 2000, 25], [4000, 4000, 4000, 44000])
        self.integrationTimes.autoMode.setVisible(False)
        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000, default=100)

        # self.builtInFilter = FilterSettings()
        self.medianFilter = SimpleFilter('Median Filter')
        self.averageFilter = SimpleFilter('Average Filter')
        self.edgeFilter = EdgeFilter(threshold=150)
        self.temporalFilter = TemporalFilter(threshold=300, factor=0.1)
        self.interferenceFilter = InterferenceFilter()
        self.builtInFilter = SettingsGroup('Built-In Filters', [self.medianFilter, self.averageFilter, self.edgeFilter, self.temporalFilter, self.interferenceFilter])


        self.roiSettings = ROISettings660(320, 240)

        #Create Layout for settings
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.guiFilterGroupBox)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.pointCloudSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)
        self.settingsLayout.addWidget(self.roiSettings)

        self.complete_setup()


def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam660()
    stream.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()