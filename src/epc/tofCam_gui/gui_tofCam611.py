import sys
import qdarktheme
import numpy as np
import argparse

from PyQt5 import QtWidgets  
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton, QComboBox
from epc.tofCam611.serialInterface import SerialInterface
from epc.tofCam611.camera import Camera
from epc.tofCam_gui.settings_widget_611 import SettingsWidget611

sys.path.append('.')

# COLORMAPS
colors = [(0,   0,   0),
          (255,   0,   0),
          (255, 255,   0),
          (0, 255,   0),
          (0, 240, 240),
          (0,   0, 255),
          (255,   0, 255)]
default = [
    (0, 0, 0),
    (51, 51, 51),
    (102, 102, 102),
    (153, 153, 153),
    (204, 204, 204),
    (255, 255, 255)
]

def startGUI(comPort):

    app = QtWidgets.QApplication(sys.argv)
    stream = Stream(comPort)
    stream.show()
    qdarktheme.setup_theme()
    sys.exit(app.exec_())


class Stream(QtWidgets.QWidget):

    def __init__(self, comPort):

        super(Stream, self).__init__()
        self.comPort = comPort
        self.initUI()

    def initUI(self):

        # ESTABLISH CONNECTION
        com = SerialInterface(self.comPort) # setup camera COM port 
        self.camera = Camera(com)

        # CAMERA DEFAULT SETTINGS
        self.camera.powerOn()
        self.camera.setModFrequency(1) # 20MHz
        self.camera.setIntTime_us(1000)

        # IMAGE VIEW
        self.imageView = pg.ImageView()
        self.imageView.setImage(np.zeros((8,8)), autoRange=False, autoHistogramRange=False, levels=(0,7500))
        self.defaultmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=default)
        self.cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)

        # DISTANCE
        self.timerdistance=QTimer()
        self.timerdistance.timeout.connect(self.updateDistance)

        # AMPLITUDE
        self.timeramp=QTimer()
        self.timeramp.timeout.connect(self.updateAmp)

        #SETTINGS
        self.settingsWidget = SettingsWidget611(self.camera)

        # IMAGE TYPE
        self.imageType = QComboBox(self)
        self.imageType.addItem("Distance")
        self.imageType.addItem("Amplitude")
        self.imageType.setCurrentIndex(0)
        self.imageType.currentIndexChanged.connect(self.imageTypeChanged)

        self.imageTypeGroupBox = QtWidgets.QGroupBox('Image Type')
        imageTypeLayout = QtWidgets.QVBoxLayout()
        imageTypeLayout.addWidget(self.imageType)
        self.imageTypeGroupBox.setLayout(imageTypeLayout)   
        self.imageTypeGroupBox.setFixedHeight(60)

        # START/STOP BUTTONS
        self.startbtn=QPushButton('Start')
        self.startbtn.clicked.connect(self.imageTypeChanged)
        self.endbtn=QPushButton('Stop')
        self.endbtn.clicked.connect(self.stopBtnClicked)
        self.startbtn.setEnabled(True)
        self.endbtn.setEnabled(False)

        self.btnGroupBox = QtWidgets.QGroupBox()
        self.btnGroupBox.setStyleSheet("QGroupBox { border: 0; }")
        btnLayout = QtWidgets.QVBoxLayout()
        btnLayout.setContentsMargins(0, 2, 0, 2)
        btnPositionLayout = QtWidgets.QGridLayout()
        self.startbtn.setFixedSize(125, 30) 
        btnPositionLayout.addWidget(self.startbtn,1,0)
        self.endbtn.setFixedSize(125, 30) 
        btnPositionLayout.addWidget(self.endbtn,1,1)   
        btnLayout.addLayout(btnPositionLayout)
        self.btnGroupBox.setLayout(btnLayout) 
        self.btnGroupBox.setFixedHeight(60)

        # GENERAL
        gridStarts = QtWidgets.QGridLayout()
        gridStarts.addWidget(self.imageTypeGroupBox,1,0)
        gridStarts.addWidget(self.btnGroupBox,2,0)
        gridStarts.addWidget(self.settingsWidget, 3,0)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(gridStarts,0,0)
        grid.addWidget(self.imageView,0,1)
        grid.setColumnStretch(1,3)
        self.setLayout(grid)

        chipID, waferID = self.camera.getChipInfo()
        fwVersion = self.camera.getFwRelease()
        self.setWindowTitle('TOF CAM 611 VIDEO STREAM                                 CHIP ID:{}     WAFER ID:{}      FW VERSION:{}.{}'
                            .format(chipID, waferID, fwVersion[0], fwVersion[1]))
        self.resize(1200,600)

    def startTimerDistance(self):
        self.endTimer()
        self.imageView.setColorMap(self.cmap)
        self.timerdistance.start(50)         

    def startTimerAmplitude(self):
        self.endTimer()
        self.imageView.setColorMap(self.cmap)
        self.timeramp.start(50)           

    def endTimer(self):
        self.timerdistance.stop()
        self.timeramp.stop()
        self.endbtn.setEnabled(True)

    def stopBtnClicked(self):
        self.endTimer()
        self.startbtn.setEnabled(True)
        self.endbtn.setEnabled(False)

    def updateDistance(self):
        img = self.camera.getDistance()
        self.imageView.setImage(img, autoRange=False, autoLevels=False, autoHistogramRange=False)

    def updateAmp(self):
        img = self.camera.getAmplitude()
        self.imageView.setImage(img, autoRange=False, autoLevels=False, autoHistogramRange=False)
      
    def imageTypeChanged(self):
    
        index = self.imageType.currentIndex()
        if index == 0:
            self.startTimerDistance()
        elif index == 1:
            self.startTimerAmplitude()
  
        self.startbtn.setEnabled(False)
        self.endbtn.setEnabled(True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start 611 GUI with COM port")
    parser.add_argument("com_port", help="COM port for camera connection (e.g., COM3)")
    args = parser.parse_args()
    startGUI(args.com_port)
