from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox, QDoubleSpinBox, QGroupBox, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from typing import List
import logging

class GroupBoxSelection(QGroupBox):
    selection_changed_signal = pyqtSignal(str)
    def __init__(self, label: str,  image_types: List[str]):
        super(GroupBoxSelection, self).__init__(label)
        self.comboBox = QComboBox(self)
        for type in image_types:
            self.comboBox.addItem(type)
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentIndexChanged.connect(self.__selection_changed)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.comboBox)
        self.setLayout(self.layout)

    def __selection_changed(self):
        self.selection_changed_signal.emit(self.comboBox.currentText())

class DropDownSetting(QGroupBox):
    signal_selection_changed = pyqtSignal(str)
    def __init__(self, label: str, setting: List[str]):
        super(DropDownSetting, self).__init__()
        self.comboBox = QComboBox(self)
        for type in setting:
            self.comboBox.addItem(type)
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentIndexChanged.connect(self.selection_changed)

        self.label = QLabel(label, self)

        self.layout = QGridLayout()
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.comboBox, 0, 1)
        self.setLayout(self.layout)
    
    def selection_changed(self):
        self.signal_selection_changed.emit(self.comboBox.currentText())

class SpinBoxSetting(QGroupBox):
    signal_value_changed = pyqtSignal(int)
    def __init__(self, label: str, min: int, max: int):
        super(SpinBoxSetting, self).__init__()
        self.spinBox = QSpinBox(self)

        self.label = QLabel(label, self)

        self.layout = QGridLayout()
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.spinBox, 0, 1)
        self.setLayout(self.layout)
        self.spinBox.valueChanged.connect(self.value_changed)
    
    def value_changed(self):
        self.signal_value_changed.emit(self.spinBox.value())

class SettingsGroup(QGroupBox):
    def __init__(self, label='', settings = []):
        super(SettingsGroup, self).__init__(label)
        self.layout = QGridLayout()
        self.settings = settings
        for row, setting in enumerate(self.settings):
            for i in range(setting.layout.count()):
                widget = setting.layout.takeAt(0).widget()
                self.layout.addWidget(widget, row, i)

        self.setLayout(self.layout)

class CheckBoxSettings(QGroupBox):
    signal_checkbox_changed = pyqtSignal(str, bool)
    def __init__(self, label: str, settings: List[str]):
        super(CheckBoxSettings, self).__init__(label)
        self.layout = QVBoxLayout()
        self.settings = settings
        for setting in self.settings:
            widget = QCheckBox(setting, self)
            widget.stateChanged.connect(lambda: self.checkbox_changed(setting, widget.isChecked()))
            self.layout.addWidget(widget)
        self.setLayout(self.layout)

    def checkbox_changed(self, text: str, state: bool):
        self.signal_checkbox_changed.emit(text, state)

class IntegrationTimes(QGroupBox):
    signal_value_changed = pyqtSignal(str, int)
    def __init__(self, labels=[], defaults=[], limits=[], min_value=0):
        super(IntegrationTimes, self).__init__('Integration Times')
        self.layout = QGridLayout()
        self.set_intTimes(labels, defaults, limits, min_value)

    def set_intTimes(self, labels=[], defaults=[], limits=[], min_value=0):
        # Clear the existing widgets
        for i in reversed(range(self.layout.count())): 
            widgetToRemove = self.layout.itemAt(i).widget()
            # remove it from the layout list
            self.layout.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

        self.layout.addWidget(QLabel(str(labels) + ' us'), 0, 0)
        for i in range(len(labels)):
            widget = QSpinBox()
            widget.setRange(min_value, limits[i])
            widget.setValue(defaults[i])
            self.layout.addWidget(widget, 0, i+1)
        self.setLayout(self.layout)

class IntegrationTimes635(QGroupBox):
    DEFAULT_INT_TIME_WOF = 125
    DEFAULT_INT_TIME_NOF = 125
    DEFAULT_INT_TIME_GRAY = 1000

    signal_value_changed = pyqtSignal(str, int)
    def __init__(self):
        super(IntegrationTimes635, self).__init__('Integration Times')
        self.layout = QGridLayout()

        self.autoMode = QCheckBox('Auto', self)
        self.autoMode.stateChanged.connect(lambda x: self.signal_value_changed.emit('auto', int(x)))
        self.layout.addWidget(self.autoMode, 0, 0)

        self.wFOV = []
        for i, text in enumerate(['WFOV1', 'WFOV2', 'WFOV3', 'WFOV4']):
            label = QLabel(text, self)
            spbox = QSpinBox(self)
            spbox.setRange(0, 1000)
            self.wFOV.append(spbox)
            self.layout.addWidget(label, i+1, 0)
            self.layout.addWidget(spbox, i+1, 1)
        self.wFOV[0].setValue(self.DEFAULT_INT_TIME_WOF)
        self.wFOV[0].valueChanged.connect(lambda x: self.signal_value_changed.emit(f'WFOV1', x))
        self.wFOV[1].valueChanged.connect(lambda x: self.signal_value_changed.emit(f'WFOV2', x))
        self.wFOV[2].valueChanged.connect(lambda x: self.signal_value_changed.emit(f'WFOV3', x))
        self.wFOV[3].valueChanged.connect(lambda x: self.signal_value_changed.emit(f'WFOV4', x))

        # Narrow field of view
        # nFOV_label = QLabel('NFOV', self)
        # self.nFOV = QSpinBox(self)
        # self.nFOV.setRange(0, 1000)
        # self.nFOV.setValue(self.DEFAULT_INT_TIME_NOF)
        # self.nFOV.valueChanged.connect(lambda x: self.signal_value_changed.emit('NFOV', x))
        # self.layout.addWidget(nFOV_label, len(self.wFOV)+1, 0)
        # self.layout.addWidget(self.nFOV, len(self.wFOV)+1, 1)

        gray_label = QLabel('Gray', self)
        self.gray = QSpinBox(self)
        self.gray.setRange(0, 50000)
        self.gray.setValue(self.DEFAULT_INT_TIME_GRAY)
        self.gray.valueChanged.connect(lambda x: self.signal_value_changed.emit('Gray', x))
        self.layout.addWidget(gray_label, len(self.wFOV)+2, 0)
        self.layout.addWidget(self.gray, len(self.wFOV)+2, 1)

        self.set_normal_mode()

        self.setLayout(self.layout)

    def set_hdr_mode(self):
        self.autoMode.setChecked(False)
        for w in self.wFOV:
            w.setEnabled(True)
        # self.nFOV.setEnabled(True)
        self.gray.setEnabled(True)

    def set_normal_mode(self):
        self.autoMode.setChecked(False)
        for w in self.wFOV:
            w.setEnabled(False)
        self.wFOV[0].setEnabled(True)
        # self.nFOV.setEnabled(True)
        self.gray.setEnabled(True)

    def set_auto_mode(self):
        self.autoMode.setChecked(True)
        for w in self.wFOV:
            w.setEnabled(False)
        # self.nFOV.setEnabled(False)
        self.gray.setEnabled(False)
        

class SimpleFilter(QtWidgets.QWidget):
    signal_filter_changed = pyqtSignal(bool)
    def __init__(self, name: str):
        super(SimpleFilter, self).__init__()
        self.layout = QHBoxLayout()
        self.checkBox = QCheckBox(name, self)
        self.layout.addWidget(self.checkBox)
        self.setLayout(self.layout)

        self.checkBox.stateChanged.connect(lambda enable: self.signal_filter_changed.emit(enable))

    def configure(self, conf: dict):
        if conf['enabled']:
            self.setVisible(True)
        else:
            self.setVisible(False)

class TemporalFilter(SimpleFilter):
    signal_filter_changed = pyqtSignal(bool, int, float)
    def __init__(self):
        super(TemporalFilter, self).__init__('TemporalFilter')
        self.thresholdLabel = QLabel('Treshold', self)
        self.threshold = QSpinBox(self)
        self.factorLabel = QLabel('Factor', self)
        self.factor = QDoubleSpinBox(self)
        self.layout.addWidget(self.thresholdLabel)
        self.layout.addWidget(self.threshold)
        self.layout.addWidget(self.factorLabel)
        self.layout.addWidget(self.factor)

        self.threshold.valueChanged.connect(lambda: self.signal_filter_changed.emit(self.checkBox.isChecked(), self.threshold.value(), self.factor.value()))
        self.factor.valueChanged.connect(lambda: self.signal_filter_changed.emit(self.checkBox.isChecked(), self.threshold.value(), self.factor.value()))
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)
    
    def __set_active(self, enable: bool):
        self.threshold.setEnabled(enable)
        self.factor.setEnabled(enable)
        self.factorLabel.setEnabled(enable)
        self.thresholdLabel.setEnabled(enable)
        self.signal_filter_changed.emit(enable, self.threshold.value(), self.factor.value())


    def configure(self, conf: dict):
        super().configure(conf)
        self.threshold.setValue(conf['threshold']['value'])
        self.threshold.setRange(conf['threshold']['min'], conf['threshold']['max'])

class EdgeFilter(SimpleFilter):
    signal_filter_changed = pyqtSignal(bool, int)
    def __init__(self):
        super(EdgeFilter, self).__init__('EdgeFilter')
        self.thresholdLabel = QLabel('Threshold', self)
        self.threshold = QSpinBox(self)
        self.layout.addWidget(self.thresholdLabel)
        self.layout.addWidget(self.threshold)

        self.threshold.valueChanged.connect(lambda: self.signal_filter_changed.emit(self.checkBox.isChecked(), self.threshold.value()))
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)

    def __set_active(self, enable: bool):
        self.threshold.setEnabled(enable)
        self.thresholdLabel.setEnabled(enable)
        self.signal_filter_changed.emit(enable, self.threshold.value())

class FilterSettings(QGroupBox):
    def __init__(self, parent=None):
        super(FilterSettings, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.medianFilter = SimpleFilter('Median Filter')
        self.averageFilter = SimpleFilter('Average Filter')
        self.edgeFilter = EdgeFilter()
        self.temporalFilter = TemporalFilter()

        self.layout.addWidget(self.medianFilter)
        self.layout.addWidget(self.averageFilter)
        self.layout.addWidget(self.edgeFilter)
        self.layout.addWidget(self.temporalFilter)

        self.setLayout(self.layout) 
    
    def configure(self, conf: dict):
        self.medianFilter.configure(conf['medianFilter'])
        self.averageFilter.setChecked(conf['averageFilter'])
        self.temporalFilter.setChecked(conf['temporalFilter'])


class RoiSettings(QGroupBox):
    signal_roi_changed = pyqtSignal(int, int, int, int)
    def __init__(self, width: int, height: int, label='ROI'):
        super(RoiSettings, self).__init__(label)
        self.layout = QGridLayout()
        self.x = QSpinBox(self)
        self.y = QSpinBox(self)
        self.width = QSpinBox(self)
        self.height = QSpinBox(self)

        self.x.setMinimum(0)
        self.x.setMaximum(width)
        self.y.setMinimum(0)
        self.y.setMaximum(height)
        self.width.setMinimum(0)
        self.width.setMaximum(width)
        self.height.setMinimum(0)
        self.height.setMaximum(height)

        self.x.setValue(0)
        self.y.setValue(0)
        self.width.setValue(width)
        self.height.setValue(height)

        self.xLabel = QLabel('X', self)
        self.yLabel = QLabel('Y', self)
        self.widthLabel = QLabel('With', self)
        self.heightLabel = QLabel('Height', self)

        self.layout.addWidget(self.xLabel, 0, 0)
        self.layout.addWidget(self.x, 0, 1)
        self.layout.addWidget(self.yLabel, 1, 0)
        self.layout.addWidget(self.y, 1, 1)
        self.layout.addWidget(self.widthLabel, 0, 2)
        self.layout.addWidget(self.width, 0, 3)
        self.layout.addWidget(self.heightLabel, 1, 2)
        self.layout.addWidget(self.height, 1, 3)

        self.x.valueChanged.connect(self.roiChanged)
        self.y.valueChanged.connect(self.roiChanged)
        self.width.valueChanged.connect(self.roiChanged)
        self.height.valueChanged.connect(self.roiChanged)

        self.setLayout(self.layout)

    def roiChanged(self):
        self.signal_roi_changed.emit(self.x.value(), self.y.value(), self.width.value(), self.height.value())

class SettingsWidget(QtWidgets.QWidget):
    def __init__(self, server):
        super(SettingsWidget, self).__init__()
        self.server = server
        self.layout = QtWidgets.QGridLayout()
        self.initIntegrationTimeSettings()
        self.initModulationSettings()
        self.initAmplitudeSettings()
        self.initFilterSettings()
        self.initHDRSettings()

    def initIntegrationTimeSettings(self):

        self.integration3DLow = QSpinBox(self)
        self.integration3DMid = QSpinBox(self)
        self.integration3DHigh = QSpinBox(self)
        self.integrationGrayScale = QSpinBox(self)

        self.integration3DLow.setMinimum(0)
        self.integration3DLow.setMaximum(4000)
        self.integration3DMid.setMinimum(0)
        self.integration3DMid.setMaximum(4000)
        self.integration3DHigh.setMinimum(0)
        self.integration3DHigh.setMaximum(4000)
        self.integrationGrayScale.setMinimum(1)
        self.integrationGrayScale.setMaximum(50000)

        # default values
        self.integration3DLow.setValue(100)
        self.integration3DMid.setValue(0)
        self.integration3DHigh.setValue(0)
        self.integrationGrayScale.setValue(1000)
        self.integration3DMid.setEnabled(False)
        self.integration3DHigh.setEnabled(False)

        # add labels
        self.integrationLabel = QLabel('[Low Mid High Grayscale] μs', self)

        # layout
        self.integrationGroupBox = QtWidgets.QGroupBox('Integration Time')
        integrationLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.integrationLabel, 0, 0)
        positionLayout.addWidget(self.integration3DLow, 0, 1)
        positionLayout.addWidget(self.integration3DMid, 0, 2)
        positionLayout.addWidget(self.integration3DHigh, 0, 3)
        positionLayout.addWidget(self.integrationGrayScale, 0, 4)
        integrationLayout.addLayout(positionLayout)
        self.integrationGroupBox.setLayout(integrationLayout) 
        self.layout.addWidget(self.integrationGroupBox, 1,0)
        self.setLayout(self.layout)

        # signals for input changes
        self.integration3DLow.valueChanged.connect(self.integrationTimeChanged)
        self.integration3DMid.valueChanged.connect(self.integrationTimeChanged)
        self.integration3DHigh.valueChanged.connect(self.integrationTimeChanged)
        self.integrationGrayScale.valueChanged.connect(self.integrationTimeChanged)

    def integrationTimeChanged(self):
        integrationTimeGrayscale = self.integrationGrayScale.value()
        integrationTime3DLow = self.integration3DLow.value()
        integrationTime3DMid = self.integration3DMid.value()
        integrationTime3DHigh = self.integration3DHigh.value()
        self.server.setIntTimesus(integrationTimeGrayscale, integrationTime3DLow, integrationTime3DMid, integrationTime3DHigh)

    def initModulationSettings(self):

        self.modulationFrequency = QComboBox(self)
        self.modulationFrequency.addItem("24 MHz")
        self.modulationFrequency.addItem("12 MHz")
        self.modulationFrequency.addItem("6 MHz")
        self.modulationFrequency.addItem("3 MHz")
        self.modulationFrequency.addItem("1.5 MHz")
        self.modulationFrequency.addItem("0.75 MHz")

        self.modulationChannel = QComboBox(self)
        self.modulationChannel.addItem("0")
        self.modulationChannel.addItem("1")
        self.modulationChannel.addItem("2")
        self.modulationChannel.addItem("3")
        self.modulationChannel.addItem("4")
        self.modulationChannel.addItem("5")
        self.modulationChannel.addItem("6")
        self.modulationChannel.addItem("7")
        self.modulationChannel.addItem("8")
        self.modulationChannel.addItem("9")
        self.modulationChannel.addItem("10")
        self.modulationChannel.addItem("11")
        self.modulationChannel.addItem("12")
        self.modulationChannel.addItem("13")
        self.modulationChannel.addItem("14")
        self.modulationChannel.addItem("15")

        # set the default selections
        self.modulationFrequency.setCurrentIndex(0)
        self.modulationChannel.setCurrentIndex(0)

        # add labels
        self.modulationFrequencyLabel = QLabel('Modulation Frequency', self)
        self.modulationChannelLabel = QLabel('Modulation Channel', self)

        # layout
        self.modulationGroupBox = QtWidgets.QGroupBox()
        modulationLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.modulationFrequencyLabel, 0, 0)
        positionLayout.addWidget(self.modulationFrequency, 0, 1)
        positionLayout.addWidget(self.modulationChannelLabel, 1, 0)
        positionLayout.addWidget(self.modulationChannel, 1, 1)
        modulationLayout.addLayout(positionLayout)
        self.modulationGroupBox.setLayout(modulationLayout) 
        self.layout.addWidget(self.modulationGroupBox, 2,0)
        self.setLayout(self.layout)

        # signals for input changes
        self.modulationFrequency.currentIndexChanged.connect(self.modulationChanged)
        self.modulationChannel.currentIndexChanged.connect(self.modulationChanged)


    def modulationChanged(self):

        frequencyIndex = self.modulationFrequency.currentIndex()
        switch = {
            0: 24,
            1: 12,
            2: 6,
            3: 3,
            4: 1.5,
            5: 0.75
        }
        commandFreqIndex = switch[frequencyIndex]
        channelIndex = self.modulationChannel.currentIndex()
        self.server.setModulationFrequencyMHz(commandFreqIndex, channelIndex)

    def initAmplitudeSettings(self):

        self.minAmplitude = QSpinBox(self)

        self.minAmplitude.setMinimum(0)
        self.minAmplitude.setMaximum(6000)

        # default value
        self.minAmplitude.setValue(0)
        self.minAmplitudeLabel = QLabel('Minimum Amplitude [LSB]', self)

        # layout
        self.settingsGroupBox = QtWidgets.QGroupBox()
        settingsLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.minAmplitudeLabel, 0, 0)
        positionLayout.addWidget(self.minAmplitude, 0, 1)
        settingsLayout.addLayout(positionLayout)
        self.settingsGroupBox.setLayout(settingsLayout) 
        self.layout.addWidget(self.settingsGroupBox, 3,0)
        self.setLayout(self.layout)

        # signals for input changes
        self.minAmplitude.valueChanged.connect(self.amplitudeChanged)

    def amplitudeChanged(self):
        self.server.setMinAmplitude(self.minAmplitude.value())

    def initFilterSettings(self):

        self.medianFilter = QCheckBox(self)
        self.averageFilter = QCheckBox(self)
        self.edgeFilter = QCheckBox(self)
        self.edgeFilterThreshold = QSpinBox(self)
        self.temporalFilter = QCheckBox(self)
        self.temporalFilterFactor = QDoubleSpinBox(self)
        self.temporalFilterThreshold = QSpinBox(self)
        self.interferenceDetect = QCheckBox(self)
        self.interferenceDetectLimit = QSpinBox(self)
        self.interferenceDetectUseLastValue = QCheckBox(self)
    
        self.medianFilter.setText("Median Filter")
        self.averageFilter.setText("Average Filter")
        self.edgeFilter.setText("Edge Filter")
        self.temporalFilter.setText("Temporal Filter")
        self.interferenceDetect.setText("Interference Detect")
        self.interferenceDetectUseLastValue.setText("Use Last Value")
        self.edgeFilterThreshold.setMinimum(0)
        self.edgeFilterThreshold.setMaximum(5000)
        self.temporalFilterFactor.setMinimum(0.00)
        self.temporalFilterFactor.setMaximum(1.00)
        self.temporalFilterFactor.setSingleStep(0.1)
        self.temporalFilterFactor.setDecimals(2)
        self.temporalFilterThreshold.setMinimum(0)
        self.temporalFilterThreshold.setMaximum(1000)
        self.interferenceDetectLimit.setMinimum(0)
        self.interferenceDetectLimit.setMaximum(1000)

        # default value
        self.edgeFilterThreshold.setValue(0)
        self.temporalFilterFactor.setValue(0.00)
        self.temporalFilterThreshold.setValue(0)
        self.interferenceDetectLimit.setValue(0)

        self.edgeFilterThresholdLabel = QLabel('Threshold [mm]', self)
        self.temporalFilterFactorLabel = QLabel('Factor', self)
        self.temporalFilterThresholdLabel = QLabel('Threshold [mm]', self)
        self.interferenceDetectLimitLabel = QLabel('Limit [LSB]', self)

        self.edgeFilterThresholdLabel.setVisible(False)
        self.edgeFilterThreshold.setVisible(False)
        self.temporalFilterFactor.setVisible(False)
        self.temporalFilterThreshold.setVisible(False)
        self.temporalFilterFactorLabel.setVisible(False)
        self.temporalFilterThresholdLabel.setVisible(False)        
        self.interferenceDetectLimit.setVisible(False)
        self.interferenceDetectUseLastValue.setVisible(False)
        self.interferenceDetectLimitLabel.setVisible(False)
    
        # group box for filters
        self.filterGroupBox = QtWidgets.QGroupBox('Camera Built-In Filters')
        filterLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.medianFilter, 0, 0)
        positionLayout.addWidget(self.averageFilter, 1, 0)
        positionLayout.addWidget(self.edgeFilter, 2, 0)
        positionLayout.addWidget(self.edgeFilterThresholdLabel, 2, 1)
        positionLayout.addWidget(self.edgeFilterThreshold, 2, 2)
        positionLayout.addWidget(self.temporalFilter, 3, 0)
        positionLayout.addWidget(self.temporalFilterFactorLabel, 3, 1)
        positionLayout.addWidget(self.temporalFilterFactor, 3, 2)
        positionLayout.addWidget(self.temporalFilterThresholdLabel, 3, 3)
        positionLayout.addWidget(self.temporalFilterThreshold, 3, 4)
        positionLayout.addWidget(self.interferenceDetect, 4, 0)
        positionLayout.addWidget(self.interferenceDetectLimitLabel, 4, 1)
        positionLayout.addWidget(self.interferenceDetectLimit, 4, 2)
        positionLayout.addWidget(self.interferenceDetectUseLastValue, 4, 3)
        filterLayout.addLayout(positionLayout)
        self.filterGroupBox.setLayout(filterLayout)   

        # layout
        self.layout.addWidget(self.filterGroupBox, 4, 0)
        self.setLayout(self.layout)

        # signals for input changes
        self.medianFilter.stateChanged.connect(self.filterChanged)
        self.averageFilter.stateChanged.connect(self.filterChanged)
        self.edgeFilter.stateChanged.connect(self.edgeFilterChanged)
        self.edgeFilterThreshold.valueChanged.connect(self.filterChanged)
        self.temporalFilter.stateChanged.connect(self.temporalFilterChanged)
        self.temporalFilterFactor.valueChanged.connect(self.filterChanged)
        self.temporalFilterThreshold.valueChanged.connect(self.filterChanged)
        self.interferenceDetect.stateChanged.connect(self.interferenceDetectChanged)
        self.interferenceDetectLimit.valueChanged.connect(self.filterChanged)
        self.interferenceDetectUseLastValue.stateChanged.connect(self.filterChanged)

    def edgeFilterChanged(self):

        if self.edgeFilter.isChecked():
            self.edgeFilterThresholdLabel.setVisible(True)
            self.edgeFilterThreshold.setVisible(True)
            self.filterChanged()
        else:
            self.edgeFilterThresholdLabel.setVisible(False)
            self.edgeFilterThreshold.setVisible(False)

            enableMedianFilter = self.medianFilter.isChecked()
            enableAverageFilter = self.averageFilter.isChecked()
            temporalFilterFactor = self.temporalFilterFactor.value()
            temporalFilterThreshold = self.temporalFilterThreshold.value()
            interferenceDetectionLimit = self.interferenceDetectLimit.value()
            interferenceDetectionUseLastValue = self.interferenceDetectUseLastValue.isChecked()
            self.server.setFilter(int(enableMedianFilter), int(enableAverageFilter), 0, 
                   int(temporalFilterFactor*1000), temporalFilterThreshold, interferenceDetectionLimit, int(interferenceDetectionUseLastValue))

    def temporalFilterChanged(self):

        if self.temporalFilter.isChecked():
            self.temporalFilterFactor.setVisible(True)
            self.temporalFilterThreshold.setVisible(True)
            self.temporalFilterFactorLabel.setVisible(True)
            self.temporalFilterThresholdLabel.setVisible(True)
            self.filterChanged()
        else:
            self.temporalFilterFactor.setVisible(False)
            self.temporalFilterThreshold.setVisible(False)
            self.temporalFilterFactorLabel.setVisible(False)
            self.temporalFilterThresholdLabel.setVisible(False)

            enableMedianFilter = self.medianFilter.isChecked()
            enableAverageFilter = self.averageFilter.isChecked()
            edgeDetectionThreshold = self.edgeFilterThreshold.value()
            interferenceDetectionLimit = self.interferenceDetectLimit.value()
            interferenceDetectionUseLastValue = self.interferenceDetectUseLastValue.isChecked()
            self.server.setFilter(int(enableMedianFilter), int(enableAverageFilter), edgeDetectionThreshold, 
                    0, 0, interferenceDetectionLimit, int(interferenceDetectionUseLastValue))
    

    def interferenceDetectChanged(self):

        if self.interferenceDetect.isChecked():
            self.interferenceDetectLimit.setVisible(True)
            self.interferenceDetectUseLastValue.setVisible(True)
            self.interferenceDetectLimitLabel.setVisible(True)
            self.filterChanged()

        else:
            self.interferenceDetectLimit.setVisible(False)
            self.interferenceDetectUseLastValue.setVisible(False)
            self.interferenceDetectLimitLabel.setVisible(False)
            enableMedianFilter = self.medianFilter.isChecked()
            enableAverageFilter = self.averageFilter.isChecked()
            edgeDetectionThreshold = self.edgeFilterThreshold.value()
            temporalFilterFactor = self.temporalFilterFactor.value()
            temporalFilterThreshold = self.temporalFilterThreshold.value()

            self.server.setFilter(int(enableMedianFilter), int(enableAverageFilter), edgeDetectionThreshold, 
                    int(temporalFilterFactor*1000), temporalFilterThreshold, 0, 0)

    def filterChanged(self):
        enableMedianFilter = self.medianFilter.isChecked()
        enableAverageFilter = self.averageFilter.isChecked()
        edgeDetectionThreshold = self.edgeFilterThreshold.value()
        temporalFilterFactor = self.temporalFilterFactor.value()
        temporalFilterThreshold = self.temporalFilterThreshold.value()
        interferenceDetectionLimit = self.interferenceDetectLimit.value()
        interferenceDetectionUseLastValue = self.interferenceDetectUseLastValue.isChecked()

        self.server.setFilter(int(enableMedianFilter), int(enableAverageFilter), edgeDetectionThreshold, 
                   int(temporalFilterFactor*1000), temporalFilterThreshold, interferenceDetectionLimit, int(interferenceDetectionUseLastValue))

    def initHDRSettings(self):

        self.hdrMode = QComboBox(self)
        self.hdrMode.addItem("HDR Off")
        self.hdrMode.addItem("HDR Spatial")
        self.hdrMode.addItem("HDR Temporal")

        # set the default selections
        self.hdrMode.setCurrentIndex(0)

        # add labels
        self.hdrModeLabel = QLabel('HDR Mode', self)

        # layout
        self.hdrGroupBox = QtWidgets.QGroupBox()
        hdrLayout = QtWidgets.QVBoxLayout()
        positionLayout = QtWidgets.QGridLayout()
        positionLayout.addWidget(self.hdrModeLabel, 0, 0)
        positionLayout.addWidget(self.hdrMode, 0, 1)
        hdrLayout.addLayout(positionLayout)
        self.hdrGroupBox.setLayout(hdrLayout) 
        self.layout.addWidget(self.hdrGroupBox, 0,0)
        self.setLayout(self.layout)

        # signals for input changes
        self.hdrMode.currentIndexChanged.connect(self.hdrChanged)

    def hdrChanged(self):

        index = self.hdrMode.currentIndex()
        if index == 0:
            self.integration3DMid.setEnabled(False)
            self.integration3DHigh.setEnabled(False)
        elif index == 1:
            self.integration3DMid.setEnabled(True)
            self.integration3DHigh.setEnabled(False)
        elif index == 2:
            self.integration3DMid.setEnabled(True)
            self.integration3DHigh.setEnabled(True)

        self.server.setHdr(index)