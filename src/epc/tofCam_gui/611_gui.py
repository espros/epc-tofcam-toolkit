import sys

sys.path.append('.')

import qdarktheme
import numpy as np

from PyQt5 import QtWidgets  
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton, QComboBox, QSpinBox, QLabel, QCheckBox, QDoubleSpinBox

from epc.tofCam611.serialInterface import SerialInterface
from epc.tofCam611.camera import Camera

#ESTABLISH CONNECTION
com = SerialInterface('COM3')
camera = Camera(com)

#CAMERA DEFAULT SETTINGS
camera.powerOn()
camera.setModFrequency(1) # 20MHz
camera.setIntTime_us(1000)

def main():

    app = QtWidgets.QApplication(sys.argv)
    qdarktheme.setup_theme()
    stream = Stream()
    stream.show()
    sys.exit(app.exec_())

class Stream(QtWidgets.QWidget):
    def __init__(self):

        super(Stream, self).__init__()
        self.initUI()

    def initUI(self):

        self.sg1_image=pg.ImageView()

        #GENERAL COLORMAPS
        colors = [  (  0,   0,   0),
                     (255,   0,   0),
                     (255, 255,   0),
                     (  0, 255,   0),
                     (  0, 240, 240),
                     (  0,   0, 255),
                     (255,   0, 255) ]

        default=  [
            (0, 0, 0),
            (51, 51, 51),
            (102, 102, 102),
            (153, 153, 153),
            (204, 204, 204),
            (255, 255, 255)
        ]

        self.defaultmap=pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=default)
        self.cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)

        # DISTANCE
        self.timerdistance=QTimer()
        self.timerdistance.timeout.connect(self.updateDistance)

        # AMPLITUDE
        self.timeramp=QTimer()
        self.timeramp.timeout.connect(self.updateAmp)

        # FILTERS
        self.temporalFilter = QCheckBox(self)
        self.temporalFilterFactor = QDoubleSpinBox(self)
        self.temporalFilterThreshold = QSpinBox(self)
    
        self.temporalFilter.setText("Temporal Filter")
        self.temporalFilterFactor.setMinimum(0.00)
        self.temporalFilterFactor.setMaximum(1.00)
        self.temporalFilterFactor.setSingleStep(0.1)
        self.temporalFilterFactor.setDecimals(3)
        self.temporalFilterFactor.setValue(0.1)
        self.temporalFilterThreshold.setMinimum(0)
        self.temporalFilterThreshold.setMaximum(20000)
        self.temporalFilterThreshold.setSingleStep(10)
        self.temporalFilterThreshold.setValue(100)
        self.temporalFilterFactorLabel = QLabel('Factor', self)
        self.temporalFilterThresholdLabel = QLabel('Threshold [mm]', self)

        self.temporalFilterFactor.setVisible(False)
        self.temporalFilterThreshold.setVisible(False)
        self.temporalFilterFactorLabel.setVisible(False)
        self.temporalFilterThresholdLabel.setVisible(False)        

        self.filterGroupBox = QtWidgets.QGroupBox('Camera Built-In Filters')
        filterLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.temporalFilter, 0, 0)
        positionLayout.addWidget(self.temporalFilterFactorLabel, 0, 1)
        positionLayout.addWidget(self.temporalFilterFactor, 0, 2)
        positionLayout.addWidget(self.temporalFilterThresholdLabel, 0, 3)
        positionLayout.addWidget(self.temporalFilterThreshold, 0, 4)
        filterLayout.addLayout(positionLayout)
        self.filterGroupBox.setLayout(filterLayout)
        self.filterGroupBox.setFixedHeight(60)          

        self.temporalFilter.stateChanged.connect(self.temporalFilterChanged)
        self.temporalFilterFactor.valueChanged.connect(self.filterValueChanged)
        self.temporalFilterThreshold.valueChanged.connect(self.filterValueChanged)

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

        # INTEGRATION TIME
        self.integration3D = QSpinBox(self)
        self.integration3D.setMinimum(0)
        self.integration3D.setMaximum(1600)
        self.integration3D.setValue(1000)
        self.integrationLabel = QLabel('(max 1600 μs)', self)

        self.integrationGroupBox = QtWidgets.QGroupBox('Integration Time')
        integrationLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.integration3D, 0, 0)
        positionLayout.addWidget(self.integrationLabel, 0, 1)
        integrationLayout.addLayout(positionLayout)
        self.integrationGroupBox.setLayout(integrationLayout) 
        self.integrationGroupBox.setFixedHeight(60)

        self.integration3D.valueChanged.connect(self.integrationTimeChanged)  

        # MODULATION
        self.modulationFrequency = QComboBox(self)
        self.modulationFrequency.addItem("10 MHz")
        self.modulationFrequency.addItem("20 MHz")
        self.modulationFrequency.setCurrentIndex(1)
        self.modulationFrequency.setEnabled(False)
        self.modulationFrequencyLabel = QLabel('Modulation Frequency', self)

        self.modulationGroupBox = QtWidgets.QGroupBox()
        modulationLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.modulationFrequencyLabel, 0, 0)
        positionLayout.addWidget(self.modulationFrequency, 0, 1)
        modulationLayout.addLayout(positionLayout)
        self.modulationGroupBox.setLayout(modulationLayout) 
        self.modulationGroupBox.setFixedHeight(60)

        self.modulationFrequency.currentIndexChanged.connect(self.modulationChanged)

        #GENERAL
        gridStarts=QtWidgets.QGridLayout()
        gridStarts.addWidget(self.imageTypeGroupBox,1,0)
        gridStarts.addWidget(self.btnGroupBox,2,0)
        gridStarts.addWidget(self.integrationGroupBox,3,0)
        gridStarts.addWidget(self.filterGroupBox,4, 0)
        gridStarts.addWidget(self.modulationGroupBox, 5,0)

        grid=QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(gridStarts,0,0)

        grid.addWidget(self.sg1_image,0,1)

        grid.setColumnStretch(1,3)

        self.setLayout(grid)

        chipID, waferID = camera.getChipInfo()
        fwVersion = camera.getFwRelease()
        self.setWindowTitle('TOF CAM 611 VIDEO STREAM                                 CHIP ID:{}     WAFER ID:{}      FW VERSION:{}.{}'
                            .format(chipID, waferID, fwVersion[0], fwVersion[1]))
        self.resize(1200,600)

        #FRAMCOUNTERS FOR EACH MODE
        #COULD BE USED E.G. TO CALCULATE FRAMERATE
        self.j=0 #DISTANCE
        self.k=0 #AMPLITUDE

    #ALL BUTTONS
    def startTimerDistance(self):
        self.endTimer()
        self.sg1_image.setColorMap(self.cmap)
        self.timerdistance.start(50)         #MIN TIME BETWEEN FRAMES

    def startTimerAmplitude(self):
        self.endTimer()
        self.sg1_image.setColorMap(self.cmap)
        self.timeramp.start(50)                #MIN TIME BETWEEN FRAMES

    def endTimer(self):
        self.timerdistance.stop()
        self.timeramp.stop()
        self.endbtn.setEnabled(True)

    def stopBtnClicked(self):
        self.endTimer()
        self.startbtn.setEnabled(True)
        self.endbtn.setEnabled(False)

     #UPDATE DISPLAYED IMAGE DEPENDING ON THE CHOSEN MODE
    def updateDistance(self):
        self.j+=1
        img = camera.getDistance()
        self.sg1_image.setImage(img)

    def updateAmp(self):
        self.k+=1
        img=camera.getAmplitude()
        self.sg1_image.setImage(img)
      
    def imageTypeChanged(self):
    
        index = self.imageType.currentIndex()
        if index == 0:
            self.startTimerDistance()
        elif index == 1:
            self.startTimerAmplitude()
  
        self.startbtn.setEnabled(False)
        self.endbtn.setEnabled(True)

    def temporalFilterChanged(self):

        if self.temporalFilter.isChecked():
            self.temporalFilterFactor.setVisible(True)
            self.temporalFilterThreshold.setVisible(True)
            self.temporalFilterFactorLabel.setVisible(True)
            self.temporalFilterThresholdLabel.setVisible(True)
        else:
            self.temporalFilterFactor.setVisible(False)
            self.temporalFilterThreshold.setVisible(False)
            self.temporalFilterFactorLabel.setVisible(False)
            self.temporalFilterThresholdLabel.setVisible(False)

    def filterValueChanged(self):
        factor = self.temporalFilterFactor.value()
        threshold = self.temporalFilterThreshold.value()
        camera.setFilter(threshold,int(factor*1000))
        
    def integrationTimeChanged(self):
        integrationTime3D = self.integration3D.value()
        camera.setIntTime_us(integrationTime3D)

    def modulationChanged(self):
        frequencyIndex = self.modulationFrequency.currentIndex()
        camera.setModFrequency(frequencyIndex)

main()
