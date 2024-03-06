from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QSpinBox, QDoubleSpinBox, QGroupBox, QVBoxLayout
from PySide6.QtCore import Signal

class SimpleFilter(QWidget):
    signal_filter_changed = Signal(bool)
    def __init__(self, name: str, default_on=False):
        super(SimpleFilter, self).__init__()
        self.default_on = default_on
        boxLayout = QHBoxLayout()
        self.checkBox = QCheckBox(name, self)
        boxLayout.addWidget(self.checkBox)
        self.setLayout(boxLayout)

        self.checkBox.stateChanged.connect(lambda enable: self.signal_filter_changed.emit(enable))

    def isChecked(self) -> bool:
        return self.checkBox.isChecked()
    
    def setDefaultValue(self):
        self.checkBox.setChecked(self.default_on)
        self.checkBox.stateChanged.emit(self.default_on)

class TemporalFilter(SimpleFilter):
    signal_filter_changed = Signal(bool, int, float)
    def __init__(self, range_threshold=(0, 1000), range_factor=(0.0, 1.0), threshold=300, factor=0.3, default_on=False):
        super(TemporalFilter, self).__init__('TemporalFilter', default_on)
        self.defaultThreshold = threshold
        self.defaultFactor = factor
        self.thresholdLabel = QLabel('Threshold [mm]', self)
        self.threshold = QSpinBox(self)
        self.threshold.setSingleStep(10)
        self.threshold.setRange(*range_threshold)
        self.factorLabel = QLabel('Factor', self)
        self.factor = QDoubleSpinBox(self)
        self.factor.setSingleStep(0.1)
        self.factor.setDecimals(2)
        self.factor.setRange(*range_factor)

        layout = self.layout()

        layout.addWidget(self.thresholdLabel)
        layout.addWidget(self.threshold)
        layout.addWidget(self.factorLabel)
        layout.addWidget(self.factor)

        self.threshold.valueChanged.connect(lambda: self.__emit_signal())
        self.factor.valueChanged.connect(lambda: self.__emit_signal())
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)

    def __emit_signal(self):
        self.signal_filter_changed.emit(self.checkBox.isChecked(), self.threshold.value(), self.factor.value())
    
    def __set_active(self, enable: bool):
        self.threshold.setEnabled(enable)
        self.factor.setEnabled(enable)
        self.factorLabel.setEnabled(enable)
        self.thresholdLabel.setEnabled(enable)
        self.__emit_signal()

    def setDefaultValue(self):
        self.checkBox.setChecked(self.default_on)
        self.threshold.setValue(self.defaultThreshold)
        self.factor.setValue(self.defaultFactor)
        self.__emit_signal()


class EdgeFilter(SimpleFilter):
    signal_filter_changed = Signal(bool, int)
    def __init__(self, range= (0, 5000), threshold=300, default_on=False):
        super(EdgeFilter, self).__init__('EdgeFilter', default_on)
        self.defaultThreshold = threshold
        self.thresholdLabel = QLabel('Threshold [mm]', self)
        self.threshold = QSpinBox(self)
        self.threshold.setRange(*range)
        self.layout().addWidget(self.thresholdLabel)
        self.layout().addWidget(self.threshold)

        self.threshold.valueChanged.connect(lambda: self.__emit_signal())
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)

    def __emit_signal(self):
        self.signal_filter_changed.emit(self.checkBox.isChecked(), self.threshold.value())

    def __set_active(self, enable: bool):
        self.threshold.setEnabled(enable)
        self.thresholdLabel.setEnabled(enable)
        self.__emit_signal()

    def setDefaultValue(self):
        self.checkBox.setChecked(self.default_on)
        self.threshold.setValue(self.defaultThreshold)
        self.__emit_signal()


class InterferenceFilter(SimpleFilter):
    signal_filter_changed = Signal(bool, int, bool)
    def __init__(self, range_limit=(0, 1000), limit=1000, useLast_on=False, default_on=False):
        super(InterferenceFilter, self).__init__('Interference Detection', default_on)
        self.defaultLimit = limit
        self.defaultUseLastOn = useLast_on
        self.limitLabel = QLabel('Limit [LSB]', self)
        self.limit = QSpinBox(self)
        self.limit.setRange(*range_limit)

        layout = self.layout()
        layout.addWidget(self.limitLabel)
        layout.addWidget(self.limit)

        self.useLastValue = QCheckBox('Use Last Value', self)
        layout.addWidget(self.useLastValue)

        self.limit.valueChanged.connect(lambda: self.__emit_signal())
        self.useLastValue.stateChanged.connect(lambda: self.__emit_signal())
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)

    def __emit_signal(self):
        self.signal_filter_changed.emit(self.checkBox.isChecked(), self.limit.value(), self.useLastValue.isChecked())

    def __set_active(self, enable: bool):
        self.limit.setEnabled(enable)
        self.limitLabel.setEnabled(enable)
        self.useLastValue.setEnabled(enable)
        self.signal_filter_changed.emit(enable, self.limit.value(), self.useLastValue.isChecked())

    def setDefaultValue(self):
        self.checkBox.setChecked(self.default_on)
        self.limit.setValue(self.defaultLimit)
        self.useLastValue.setChecked(self.defaultUseLastOn)
        self.__emit_signal()