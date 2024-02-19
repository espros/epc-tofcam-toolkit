from PyQt5 import QtWidgets  
from PyQt5.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox, QDoubleSpinBox

class SettingsWidget611(QtWidgets.QWidget):
    def __init__(self, server):
        super(SettingsWidget611, self).__init__()
        self.server = server
        self.layout = QtWidgets.QGridLayout()
        self.initIntegrationTimeSettings()
        self.initModulationSettings()
        self.initFilterSettings()

    def initIntegrationTimeSettings(self):
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
        self.layout.addWidget(self.integrationGroupBox,1,0)
        self.setLayout(self.layout)

        self.integration3D.valueChanged.connect(self.integrationTimeChanged) 

    def initModulationSettings(self):

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
        self.layout.addWidget(self.modulationGroupBox, 3,0)
        self.setLayout(self.layout)

        self.modulationFrequency.currentIndexChanged.connect(self.modulationChanged)        

    def initFilterSettings(self):

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
        self.layout.addWidget(self.filterGroupBox,3, 0)
        self.setLayout(self.layout)
        
        self.temporalFilter.stateChanged.connect(self.temporalFilterChanged)
        self.temporalFilterFactor.valueChanged.connect(self.filterValueChanged)
        self.temporalFilterThreshold.valueChanged.connect(self.filterValueChanged)

    def temporalFilterChanged(self):

        if self.temporalFilter.isChecked():
            self.temporalFilterFactor.setVisible(True)
            self.temporalFilterThreshold.setVisible(True)
            self.temporalFilterFactorLabel.setVisible(True)
            self.temporalFilterThresholdLabel.setVisible(True)
            self.filterValueChanged()
        else:
            self.temporalFilterFactor.setVisible(False)
            self.temporalFilterThreshold.setVisible(False)
            self.temporalFilterFactorLabel.setVisible(False)
            self.temporalFilterThresholdLabel.setVisible(False)

    def filterValueChanged(self):
        factor = self.temporalFilterFactor.value()
        threshold = self.temporalFilterThreshold.value()
        self.server.setFilter(threshold,int(factor*1000))

    def integrationTimeChanged(self):
        integrationTime3D = self.integration3D.value()
        self.server.setIntTime_us(integrationTime3D)

    def modulationChanged(self):
        frequencyIndex = self.modulationFrequency.currentIndex()
        self.server.setModFrequency(frequencyIndex)
