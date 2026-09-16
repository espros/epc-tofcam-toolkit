import numpy as np
from typing import List, Optional, Any
from PySide6.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox, QLineEdit, QSlider
from PySide6.QtWidgets import QSpinBox, QLabel, QComboBox, QCheckBox,  QGroupBox, QGridLayout, QDoubleSpinBox
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QDoubleValidator, QMouseEvent


class CameraSetting(QGroupBox):
    def __init__(self, label, settings, default, parent=None):
        super(CameraSetting, self).__init__(label, parent)
        if default is not None:
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

class CheckBoxSetting(CameraSetting):
    signal_value_changed = Signal(bool)
    def __init__(self, label: str, default: Optional[bool]=None, parent=None):
        super(CheckBoxSetting, self).__init__('', [False, True], default, parent)
        self.checkBox = QCheckBox(text=label, parent=self)
        self.gridLayout.addWidget(self.checkBox)
        self.checkBox.stateChanged.connect(lambda: self.signal_value_changed.emit(self.checkBox.isChecked()))

    def setValue(self, setting: bool):
        self.checkBox.setChecked(setting)
        self.checkBox.stateChanged.emit(setting)

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

class DoubleSpinBoxSetting(CameraSetting):
    signal_value_changed = Signal(float)
    def __init__(self, label: str, minvalue: float, maxValue: float, default: Optional[float]=None,
                 parent=None, step: float = 0.1, decimals: int = 1):
        super(DoubleSpinBoxSetting, self).__init__('', [minvalue, maxValue], default, parent)
        self.spinBox = QDoubleSpinBox(parent)
        self.spinBox.setRange(minvalue, maxValue)
        self.spinBox.setSingleStep(step)
        self.spinBox.setDecimals(decimals)
        self.label = QLabel(label, self)
        self.gridLayout.addWidget(self.label, 0, 0)
        self.gridLayout.addWidget(self.spinBox, 0, 1)
        self.spinBox.valueChanged.connect(lambda: self.signal_value_changed.emit(self.spinBox.value()))

    def setValue(self, setting: float):
        self.spinBox.setValue(setting)
        self.spinBox.valueChanged.emit(setting)

class FloatInput(CameraSetting):
    signal_value_changed = Signal(float)
    def __init__(self, label: str, minvalue: float, maxValue: float, default: Optional[float]=None, parent=None):
        super(FloatInput, self).__init__('', [minvalue, maxValue], default, parent)
        self.input = QLineEdit(parent)
        self.input.setValidator(QDoubleValidator(minvalue, maxValue, 2))
        self.label = QLabel(label, self)
        self.gridLayout.addWidget(self.label, 0, 0)
        self.gridLayout.addWidget(self.input, 0, 1)
        self.input.editingFinished.connect(lambda: self.signal_value_changed.emit(float(self.input.text())))
    
    def setValue(self, setting: int):
        self.input.setText(str(setting))
        # self.spinBox.valueChanged.emit(setting)

class _TouchSlider(QSlider):
    """
    Horizontal QSlider that is easier to use on touch screens.

    When a click misses the handle, the handle jumps to that position instead.
    This way, the handle can be dragged by clicking anywhere on the widget,
    instead of having to hit the handle precisely.

    To get the best effect, use self.setMinimumHeight(50) or similar
    to increase the size of the clickable area.
    """

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(True)
            self._set_value_from_position(event.position().x())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.isSliderDown():
            self._set_value_from_position(event.position().x())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _set_value_from_position(self, x):
        ratio = x / self.width()
        ratio = max(0.0, min(1.0, ratio))

        value = self.minimum() + ratio * (
            self.maximum() - self.minimum()
        )

        self.setValue(round(value))


class SliderSetting(CameraSetting):
    signal_value_changed = Signal(int)
    def __init__(self, label: str, minvalue: int, maxValue: int, default: Optional[int]=None, parent=None, valueFormat="{:<4d}"):
        super(SliderSetting, self).__init__('', [minvalue, maxValue], default, parent)
        self.slider = _TouchSlider(Qt.Horizontal, parent)
        self.slider.setRange(minvalue, maxValue)
        self.slider.setMinimumHeight(50)
        self.label = QLabel(label, self)
        self.valueFormat = valueFormat
        self.spinBox = QSpinBox(self)
        self.spinBox.setRange(minvalue, maxValue)
        if default is not None:
            self.spinBox.setValue(default)
        self.gridLayout.addWidget(self.label, 0, 0)
        self.gridLayout.addWidget(self.slider, 0, 1)
        self.gridLayout.addWidget(self.spinBox, 0, 2)
        # Keep slider and spinbox in sync
        self.spinBox.valueChanged.connect(self.slider.setValue)
        self.slider.sliderReleased.connect(lambda: self.spinBox.setValue(self.slider.value()))
        # Emit signal when value changed
        self.spinBox.valueChanged.connect(self.signal_value_changed.emit)

    def value(self) -> int:
        return self.slider.value()

    def setValue(self, setting: int):
        self.slider.setValue(setting)
        self.spinBox.setValue(setting)
        self.signal_value_changed.emit(setting)

class IntegrationTimes(CameraSetting):
    signal_value_changed = Signal(str, int)
    def __init__(self, labels=[], defaults=[], limits=[], min_value=0, parent=None):
        super(IntegrationTimes, self).__init__('Integration Times [us]', labels, defaults, parent)
        self.autoMode = QCheckBox('Auto', parent)
        self.autoMode.stateChanged.connect(lambda x: self.signal_value_changed.emit('auto', int(self.autoMode.isChecked())))
        self.gridLayout.addWidget(self.autoMode, 0, 0)
        self.sliders = []
        self.labels = labels

        for i, entry in enumerate(labels):
            slider = SliderSetting(entry, min_value, limits[i], defaults[i], parent)
            slider.setValue(defaults[i])
            slider.signal_value_changed.connect(self.__emit_signal)
            self.sliders.append(slider) 
            self.gridLayout.addWidget(slider, i+1, 1)

    def __emit_signal(self, value: int):
        sender = self.sender()
        for index, slider in enumerate(self.sliders):
            if slider == sender:
                self.signal_value_changed.emit(self.labels[index], self.sliders[index].value())
        
    def setTimeEnabled(self, index: int, enabled: bool):
        self.sliders[index].setEnabled(enabled)

    def getTimeAtIndex(self, index: int) -> int:
        return self.sliders[index].value()
    
    def setValue(self, index: int, value: int):
        self.sliders[index].setValue(value)
        self.sliders[index].slider.valueChanged.emit(value)

    def setDefaultValue(self):
        for i, slider in enumerate(self.sliders):
            slider.setValue(self.default[i])
            slider.slider.valueChanged.emit(self.default[i])

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
