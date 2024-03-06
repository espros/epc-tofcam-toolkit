import numpy as np
from typing import List, Optional, Any
from PySide6.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox
from PySide6.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox,  QGroupBox, QVBoxLayout, QGridLayout
from PySide6.QtCore import Signal


class CameraSetting(QGroupBox):
    def __init__(self, label, settings, default, parent=None):
        super(CameraSetting, self).__init__(label, parent)
        if default:
            self.default = default
        else:
            self.default = settings[0]
        self.settings = settings
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)

    def setDefaultValue(self):
        self.setValue(self.default)

    def setValue(self, *args, **kwargs):
        raise NotImplementedError('This method must be implemented in the derived class')
    

class GroupBoxSelection(CameraSetting):
    signal_value_changed = Signal(str)
    def __init__(self, label: str,  settings: List[str], default: Optional[str]=None, parent=None):
        super(GroupBoxSelection, self).__init__(label, settings, default, parent)
        self.comboBox = QComboBox(parent)
        for type in settings:
            self.comboBox.addItem(type)
        self.comboBox.currentIndexChanged.connect(lambda: self.signal_value_changed.emit(self.comboBox.currentText()))
        self.gridLayout.addWidget(self.comboBox, 0, 0)

    def getSelection(self) -> str:
        return self.comboBox.currentText()

    def setValue(self, setting: str):
        index = self.comboBox.findText(setting)
        if index < 0:
            raise ValueError(f'Invalid setting: {setting}')
        self.comboBox.setCurrentIndex(index)
        self.comboBox.currentIndexChanged.emit(index)


class DropDownSetting(GroupBoxSelection):
    signal_value_changed = Signal(str)
    def __init__(self, label: str, setting: List[str], default: Optional[str]=None, parent=None):
        super(DropDownSetting, self).__init__('', setting, default, parent)
        self.gridLayout.addWidget(QLabel(label, self), 0, 0)
        self.gridLayout.addWidget(self.comboBox, 0, 1)


class SpinBoxSetting(CameraSetting):
    signal_value_changed = Signal(int)
    def __init__(self, label: str, minvalue: int, maxValue: int, default: Optional[int]=None, parent=None):
        super(SpinBoxSetting, self).__init__('', [minvalue, maxValue], default, parent)
        self.spinBox = QSpinBox(parent)
        self.spinBox.setRange(minvalue, maxValue)
        self.label = QLabel(label, self)
        self.gridLayout.addWidget(self.label, 0, 0)
        self.gridLayout.addWidget(self.spinBox, 0, 1)
        self.spinBox.valueChanged.connect(lambda: self.signal_value_changed.emit(self.spinBox.value()))
    
    def setValue(self, setting: int):
        self.spinBox.setValue(setting)
        self.spinBox.valueChanged.emit(setting)


class IntegrationTimes(CameraSetting):
    signal_value_changed = Signal(str, int)
    def __init__(self, labels=[], defaults=[], limits=[], min_value=0, parent=None):
        super(IntegrationTimes, self).__init__('Integration Times [us]', labels, defaults, parent)
        self.autoMode = QCheckBox('Auto', parent)
        self.autoMode.stateChanged.connect(lambda x: self.signal_value_changed.emit('auto', int(self.autoMode.isChecked())))
        self.gridLayout.addWidget(self.autoMode, 0, 0)
        self.spinBoxes = []
        self.labels = labels

        for i, entry in enumerate(labels):
            label = QLabel(entry, parent)
            spbox = QSpinBox(parent)
            spbox.setRange(min_value, limits[i])
            spbox.setValue(defaults[i])
            spbox.valueChanged.connect(self.__emit_signal)
            self.spinBoxes.append(spbox) 
            self.gridLayout.addWidget(label, i+1, 0)
            self.gridLayout.addWidget(spbox, i+1, 1)

    def __emit_signal(self, value: int):
        sender = self.sender()
        for index, sp in enumerate(self.spinBoxes):
            if sp == sender:
                self.signal_value_changed.emit(self.labels[index], self.spinBoxes[index].value())
        
    def setTimeEnabled(self, index: int, enabled: bool):
        self.spinBoxes[index].setEnabled(enabled)

    def getTimeAtIndex(self, index: int) -> int:
        return self.spinBoxes[index].value()
    
    def setValue(self, index: int, value: int):
        self.spinBoxes[index].setValue(value)
        self.spinBoxes[index].valueChanged.emit(value)

    def setDefaultValue(self):
        for i, spinBox in enumerate(self.spinBoxes):
            spinBox.setValue(self.default[i])
            spinBox.valueChanged.emit(self.default[i])

class SettingsGroup(QGroupBox):
    def __init__(self, label='', settings: List=[]):
        super(SettingsGroup, self).__init__(label)
        self.gridLayout = QGridLayout()
        self.settings = settings
        for row, setting in enumerate(self.settings):
            for i in range(setting.layout().count()):
                widget = setting.layout().takeAt(0).widget()
                self.gridLayout.addWidget(widget, row, i)
        self.setLayout(self.gridLayout)

    def setDefaultValue(self):
        for setting in self.settings:
            setting.setDefaultValue()