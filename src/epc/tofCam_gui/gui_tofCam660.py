import qdarktheme
import sys

from PySide6 import QtWidgets  
from PySide6.QtGui import QIcon, QAction
from epc.tofCam_gui.settings_widget import ToolBar, IntegrationTimes635, FilterSettings, GroupBoxSelection, DropDownSetting, SettingsGroup, SpinBoxSetting, RoiSettings, IntegrationTimes
from epc.tofCam_gui.video_widget import VideoWidget

from epc.tofCam635 import TofCam635

from epc.tofCam_gui import transformations


class GUI_TOFcam660(QtWidgets.QMainWindow):
    def __init__(self, title='TOF CAM 660 VIDEO STREAM', parent=None):
        super(GUI_TOFcam660, self).__init__()
        self.setWindowTitle(title)

        # Create the toolbar
        self.toolBar = ToolBar(self)
        self.addToolBar(self.toolBar)

        # Create the video widget
        self.imageView = VideoWidget()
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale'])
        self.guiFilterGroupBox = GroupBoxSelection('GUI Filters', ['None'])
        self.integrationTimes = IntegrationTimes(['Low', 'Mid', 'High', 'Gray'], defaults=[100, 0, 0, 1000], limits=4*[10000])
        self.hdrModeDropDown = DropDownSetting('HDR Mode', ['HDR Off', 'HDR Spatial', 'HDR Temporal'])
        self.modulationChannel = DropDownSetting('Modulation Channel', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15'])
        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['24 MHz', '12 MHz', '6 MHz', '3 MHz', '1.5 MHz', '0.75 MHz'])
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency, self.modulationChannel, self.hdrModeDropDown])
        self.integrationTimes = IntegrationTimes(['Low', 'Mid', 'High', 'Grayscale'], [100, 1000, 2000, 50000], [4000, 4000, 4000, 50000])
        self.integrationTimes.autoMode.setVisible(False)
        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000)
        self.builtInFilter = FilterSettings()
        self.roiSettings = RoiSettings(320, 240)

        #Create Layout for settings
        self.settingsLayout = QtWidgets.QVBoxLayout()
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.guiFilterGroupBox)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)
        self.settingsLayout.addWidget(self.roiSettings)

        #Create main layout
        self.mainLayout=QtWidgets.QGridLayout()
        self.mainLayout.setSpacing(10)
        self.mainLayout.addLayout(self.settingsLayout,0,0)
        self.mainLayout.addWidget(self.imageView,0,1)
        self.mainLayout.setColumnStretch(1,3)

        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(self.mainLayout)
        self.setCentralWidget(self.widget)

        self.resize(1200,600)

def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam660()
    stream.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()