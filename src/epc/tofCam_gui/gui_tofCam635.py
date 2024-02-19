import qdarktheme
import numpy as np
import cv2
import sys

from PyQt5 import QtWidgets  
import pyqtgraph as pg
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton, QComboBox, QToolBar, QPushButton, QAction, QLabel, QWidget, QSizePolicy, QGridLayout
from epc.tofCam_gui.roi_widget import ROIWidget
from epc.tofCam_gui.settings_widget import SettingsWidget, FilterSettings, IntegrationTimes635, GroupBoxSelection, DropDownSetting, SettingsGroup, SpinBoxSetting, CheckBoxSettings, RoiSettings, IntegrationTimes
from epc.tofCam_gui.video_widget import VideoWidget

from epc.tofCam635 import TofCam635

from epc.tofCam_gui import transformations

class ToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # assemble play button
        self._startIcon = QIcon('src/epc/tofCam_gui/icons/play-start.png')
        self._stopIcon = QIcon('src/epc/tofCam_gui/icons/play-stop.png')
        self.playButton = QAction(self._startIcon, "Start", self)
        self.playButton.setStatusTip('Start and Stop live Stream')
        self.playButton.setCheckable(True)
        self.playButton.triggered.connect(lambda: self.__setIcon(self.playButton, self._startIcon, self._stopIcon))

        # assemble capture button
        self.captureButton = QAction(QIcon('src/epc/tofCam_gui/icons/capture.png'), "Capture", self)
        self.captureButton.setStatusTip('Capture a single frame')
        
        # assemble chip info and fps info
        self.chipInfo = QLabel('Chip ID:\t000\nWafer ID:\t000')
        self.fpsInfo = QLabel('FPS: 0')

        # Create the spacers
        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


        self.addAction(self.playButton)
        self.addAction(self.captureButton)
        self.addWidget(left_spacer)
        self.addWidget(self.chipInfo)
        self.addWidget(right_spacer)
        self.addWidget(self.fpsInfo)

    def setFPS(self, fps):
        self.fpsInfo.setText(f'FPS: {fps}')

    def __setIcon(self, button: QAction, on: QIcon, off: QIcon):
        if button.isChecked():
            button.setIcon(off)
        else:
            button.setIcon(on)

    def setChipInfo(self, chipID, waferID):
        self.chipInfo.setText(f'Chip ID:\t{chipID}\nWafer ID:\t{waferID}')


class GUI_TOFcam635(QtWidgets.QMainWindow):
    def __init__(self, title='TOF CAM 635 VIDEO STREAM', parent=None):
        super(GUI_TOFcam635, self).__init__()
        self.setWindowTitle(title)

        self.toolBar = ToolBar()
        self.addToolBar(self.toolBar)

        play = QAction('Play', self)
        play.setIcon(QIcon('play.png'))
        self.toolBar.addAction(play)

        self.imageView = VideoWidget()

        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale'])
        # self.guiFilterGroupBox = GroupBoxSelection('GUI Filters', ['None', 'Gradient Image', 'Thresholded Image', 'Edge Detector'])
        self.guiFilterGroupBox = GroupBoxSelection('GUI Filters', ['None'])

        self.hdrModeDropDown = DropDownSetting('HDR Mode', ['HDR Off', 'HDR Spatial', 'HDR Temporal'])
        self.modulationChannel = DropDownSetting('Modulation Channel', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15'])
        self.operationMode = DropDownSetting('Operation Mode', ['WFO'])
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationChannel, self.operationMode, self.hdrModeDropDown])
        
        self.integrationTimes = IntegrationTimes635()

        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000)
        self.builtInFilter = FilterSettings()
        self.roiSettings = RoiSettings(160, 60)

        #GENERAL
        self.settingsLayout = QtWidgets.QVBoxLayout()
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.guiFilterGroupBox)
        # self.settingsLayout.addWidget(self.hdrModeDropDown)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)
        self.settingsLayout.addWidget(self.roiSettings)


        self.mainLayout=QtWidgets.QGridLayout()
        self.mainLayout.setSpacing(10)
        self.mainLayout.addLayout(self.settingsLayout,0,0)

        self.mainLayout.addWidget(self.imageView,0,1)

        self.mainLayout.setColumnStretch(1,3)

        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(self.mainLayout)

        self.setCentralWidget(self.widget)

        self.resize(1200,600)

    def replaceSettingsWidget(self, oldWidget, newWidget):
        index = self.settingsLayout.indexOf(oldWidget)
        if index == -1:
            raise ValueError('The old widget is not in the layout')
        self.settingsLayout.removeWidget(oldWidget)
        oldWidget.setParent(None)
        self.settingsLayout.insertWidget(index, newWidget)
        
def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam635()
    stream.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()