import numpy as np
from typing import List
from PySide6.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox
from PySide6.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox,  QGroupBox, QVBoxLayout, QGridLayout
from PySide6.QtCore import Signal


class GroupBoxSelection(QGroupBox):
    selection_changed_signal = Signal(str)
    def __init__(self, label: str,  image_types: List[str], parent=None):
        super(GroupBoxSelection, self).__init__(label, parent)
        self.comboBox = QComboBox(parent)
        for type in image_types:
            self.comboBox.addItem(type)
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentIndexChanged.connect(self.__selection_changed)

        self.boxLayout = QVBoxLayout()
        self.boxLayout.addWidget(self.comboBox)
        self.setLayout(self.boxLayout)

    def __selection_changed(self):
        self.selection_changed_signal.emit(self.comboBox.currentText())

class DropDownSetting(QGroupBox):
    signal_selection_changed = Signal(str)
    def __init__(self, label: str, setting: List[str]):
        super(DropDownSetting, self).__init__()
        self.comboBox = QComboBox(self)
        for type in setting:
            self.comboBox.addItem(type)
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentIndexChanged.connect(self.selection_changed)

        self.label = QLabel(label, self)

        self.boxLayout = QGridLayout()
        self.boxLayout.addWidget(self.label, 0, 0)
        self.boxLayout.addWidget(self.comboBox, 0, 1)
        self.setLayout(self.boxLayout)

    def getSelection(self) -> str:
        return self.comboBox.currentText()
    
    def selection_changed(self):
        self.signal_selection_changed.emit(self.comboBox.currentText())

class CheckBoxSetting(QGroupBox):
    def __init__(self, label: str, parent=None):
        super(CheckBoxSetting, self).__init__(label, parent)
        self.checkBox = QCheckBox(label, parent)
        self.boxLayout = QVBoxLayout()
        self.boxLayout.addWidget(self.checkBox)
        self.setLayout(self.boxLayout)

class SpinBoxSetting(QGroupBox):
    signal_value_changed = Signal(int)
    def __init__(self, label: str, min: int, max: int, parent=None):
        super(SpinBoxSetting, self).__init__(parent)
        self.spinBox = QSpinBox(parent)

        self.label = QLabel(label, self)

        self.gridLayout = QGridLayout()
        self.gridLayout.addWidget(self.label, 0, 0)
        self.gridLayout.addWidget(self.spinBox, 0, 1)
        self.setLayout(self.gridLayout)
        self.spinBox.valueChanged.connect(self.value_changed)
    
    def value_changed(self):
        self.signal_value_changed.emit(self.spinBox.value())

class SettingsGroup(QGroupBox):
    def __init__(self, label='', settings = []):
        super(SettingsGroup, self).__init__(label)
        self.gridLayout = QGridLayout()
        self.settings = settings
        for row, setting in enumerate(self.settings):
            for i in range(setting.layout.count()):
                widget = setting.layout.takeAt(0).widget()
                self.gridLayout.addWidget(widget, row, i)

        self.setLayout(self.gridLayout)

class IntegrationTimes(QGroupBox):
    signal_value_changed = Signal(str, int)
    def __init__(self, labels=[], defaults=[], limits=[], min_value=0, parent=None):
        super(IntegrationTimes, self).__init__('Integration Times [us]')
        self.gridLayout = QGridLayout()

        self.autoMode = QCheckBox('Auto', parent)
        self.autoMode.stateChanged.connect(lambda x: self.signal_value_changed.emit('auto', int(self.autoMode.isChecked())))
        self.gridLayout.addWidget(self.autoMode, 0, 0)

        self.spinBoxes = []

        for i, entry in enumerate(labels):
            label = QLabel(entry, parent)
            spbox = QSpinBox(parent)
            spbox.setRange(min_value, limits[i])
            spbox.setValue(defaults[i])
            spbox.valueChanged.connect(lambda x: self.signal_value_changed.emit(entry, x))
            self.spinBoxes.append(spbox) 
            self.gridLayout.addWidget(label, i+1, 0)
            self.gridLayout.addWidget(spbox, i+1, 1)
        
        self.setLayout(self.gridLayout)

    def setTimeEnabled(self, index: int, enabled: bool):
        self.spinBoxes[index].setEnabled(enabled)

    def getTimeAtIndex(self, index: int) -> int:
        return self.spinBoxes[index].value()