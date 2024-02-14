import qdarktheme
import numpy as np
import cv2
import sys

from PyQt5 import QtWidgets  
import pyqtgraph as pg
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton, QComboBox, QToolBar, QPushButton, QAction
from epc.tofCam_gui.roi_widget import ROIWidget
from epc.tofCam_gui.settings_widget import SettingsWidget, GroupBoxSelection, DropDownSetting, SettingsGroup, SpinBoxSetting, CheckBoxSettings, RoiSettings, IntegrationTimes

from epc.tofCam635 import TofCam635

from epc.tofCam_gui import transformations

class ToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._startIcon = QIcon('src/epc/tofCam_gui/icons/play-start.png')
        self._stopIcon = QIcon('src/epc/tofCam_gui/icons/play-stop.png')
        self.playButton = QAction(self._startIcon, "Start", self)
        self.playButton.setStatusTip('Start and Stop live Stream')
        self.playButton.setCheckable(True)
        
        self.addAction(self.playButton)

        self.playButton.triggered.connect(lambda: self.__setIcon(self.playButton, self._startIcon, self._stopIcon))

    def __setIcon(self, button: QAction, on: QIcon, off: QIcon):
        if button.isChecked():
            button.setIcon(off)
        else:
            button.setIcon(on)

class GUI_TOFcam635(QtWidgets.QMainWindow):
    def __init__(self):

        super(GUI_TOFcam635, self).__init__()

        self.toolBar = ToolBar()
        self.addToolBar(self.toolBar)

        play = QAction('Play', self)
        play.setIcon(QIcon('play.png'))
        self.toolBar.addAction(play)

        self.mode='default'
        #GENERAL
        self.sg1_image=pg.ImageView()
        #self.sg1_image.setImage(gray)
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

        self.imageTypeGroupBox = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale'])
        self.guiFilterGroupBox = GroupBoxSelection('GUI Filters', ['None', 'Gradient Image', 'Thresholded Image', 'Edge Detector'])
        self.hdrModeDropDown = DropDownSetting('HDR Mode', ['HDR Off', 'HDR Spatial', 'HDR Temporal'])

        self.integrationTimes = IntegrationTimes(['Low', 'Mid', 'High', 'Gray'], defaults=[100, 0, 0, 1000], limits=4*[10000])

        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['24 MHz', '12 MHz', '6 MHz', '3 MHz', '1.5 MHz', '0.75 MHz'])
        self.modulationChannel = DropDownSetting('Modulation Channel', ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15'])
        self.modulationGroup = SettingsGroup('', [self.modulationFrequency, self.modulationChannel])

        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000)
        self.builtInFilter = CheckBoxSettings('Camera Built-in Filter', ['Median Filter', 'Average Filter', 'Edge Filter', 'Temporal Filter', 'Interference Detection'])
        self.roiSettings = RoiSettings(320, 240)

        #GENERAL
        gridStarts=QtWidgets.QVBoxLayout()
        gridStarts.addWidget(self.imageTypeGroupBox)
        gridStarts.addWidget(self.guiFilterGroupBox)
        gridStarts.addWidget(self.hdrModeDropDown)
        gridStarts.addWidget(self.integrationTimes)
        gridStarts.addWidget(self.modulationGroup)
        gridStarts.addWidget(self.minAmplitude)
        gridStarts.addWidget(self.builtInFilter)
        gridStarts.addWidget(self.roiSettings)


        grid=QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addLayout(gridStarts,0,0)

        grid.addWidget(self.sg1_image,0,1)

        grid.setColumnStretch(1,3)

        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(grid)

        self.setCentralWidget(self.widget)

        # chipID = server.getChipId()
        # waferID = server.getWaferId()
        # fwVersion = server.getFirmwareVersion() 
        # self.setWindowTitle('TOF CAM 660 VIDEO STREAM                                 CHIP ID:{}     WAFER ID:{}      FW VERSION:{}.{}'
        #                     .format(chipID, waferID, fwVersion['major'], fwVersion['minor']))
        self.resize(1200,600)

        #FRAMCOUNTERS FOR EACH MODE
        #COULD BE USED E.G. TO CALCULATE FRAMERATE
        self.i=0 #GREYSCALE
        self.j=0 #DISTANCE
        self.k=0 #AMPLITUDE

    #ALL BUTTONS
    def startTimerGrsc(self):
        self.endTimer()
        self.sg1_image.setColorMap(self.defaultmap)
        self.timerGrsc.start(20)            #MIN TIME BETWEEN FRAMES

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
        self.timerGrsc.stop()
        self.timeramp.stop()
        self.endbtn.setEnabled(True)

    def stopBtnClicked(self):
        self.endTimer()
        self.startbtn.setEnabled(True)
        self.endbtn.setEnabled(False)

     #UPDATE DISPLAYED IMAGE DEPENDING ON THE CHOSEN MODE
    def updateGrsc(self):
        # self.i+=1
        # img=np.rot90(server.getGrayscaleAmplitude()[0],1,(1,0))
        # img = img / img.max()
        # img=255*img
        # img=img.astype(np.uint8)
        # if(self.mode!='default'):
        #     if(self.mode=='grad'):
        #         img=transformations.gradimg(img)
        #     if(self.mode=='thresh'):
        #         img=transformations.threshgrad(img)
        #     if(self.mode=='canny'):
        #         img=cv2.Canny(img,100,50)

        # self.sg1_image.setImage(img)
        pass

    def updateDistance(self):
        # self.j+=1
        # img=np.rot90(server.getTofDistance()[0],1,(1,0))
        # img = img / img.max()
        # img=255*img
        # img=img.astype(np.uint8)
        # if(self.mode!='default'):
        #     if(self.mode=='grad'):
        #         img=transformations.gradimg(img)
        #     if(self.mode=='thresh'):
        #         img=transformations.threshgrad(img)
        #     if(self.mode=='canny'):
        #         img=cv2.Canny(img,700,600)
        # self.sg1_image.setImage(img)
        pass


    def updateAmp(self):
        # self.k+=1
        # img=np.rot90(server.getTofAmplitude()[0],1,(1,0))
        # img = img / img.max()
        # img=255*img
        # img=img.astype(np.uint8)
        # if(self.mode!='default'):
        #     if(self.mode=='grad'):
        #         img=transformations.gradimg(img)
        #     if(self.mode=='thresh'):
        #         img=transformations.threshgrad(img)
        #     if(self.mode=='canny'):
        #         img=cv2.Canny(img,220,110)
        # self.sg1_image.setImage(img)
        pass

    def guiFilterChanged(self):
    
        filterIndex = self.guiFilters.currentIndex()
        switch = {
            0: 'default',
            1: 'grad',
            2: 'thresh',
            3: 'canny',
        }
        self.mode = switch[filterIndex]
        
    def imageTypeChanged(self):
    
        index = self.imageType.currentIndex()
        if index == 0:
            self.startTimerDistance()
        elif index == 1:
            self.startTimerAmplitude()
        elif index == 2:
            self.startTimerGrsc()
        
        self.startbtn.setEnabled(False)
        self.endbtn.setEnabled(True)
        
def main():
    # ESTABLISH CONNECTION
    cam_instance = TofCam635()
    cam = cam_instance.cmd

    # Camera settings
    cam.setModFrequency(0)
    cam.setBinning(False)
    

    #OPEN THE QTGUI DEFINED BELOW
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_TOFcam635()
    stream.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()