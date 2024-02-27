from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QSpinBox, QDoubleSpinBox, QGroupBox, QVBoxLayout
from PySide6.QtCore import Signal

class SimpleFilter(QWidget):
    signal_filter_changed = Signal(bool)
    def __init__(self, name: str):
        super(SimpleFilter, self).__init__()
        self.layout = QHBoxLayout()
        self.checkBox = QCheckBox(name, self)
        self.layout.addWidget(self.checkBox)
        self.setLayout(self.layout)

        self.checkBox.stateChanged.connect(lambda enable: self.signal_filter_changed.emit(enable))

    def isChecked(self) -> bool:
        return self.checkBox.isChecked()

class TemporalFilter(SimpleFilter):
    signal_filter_changed = Signal(bool, int, float)
    def __init__(self):
        super(TemporalFilter, self).__init__('TemporalFilter')
        self.thresholdLabel = QLabel('Threshold', self)
        self.threshold = QSpinBox(self)
        self.threshold.setSingleStep(10)
        self.threshold.setRange(0, 1000)
        self.factorLabel = QLabel('Factor', self)
        self.factor = QDoubleSpinBox(self)
        self.factor.setSingleStep(0.1)
        self.factor.setDecimals(2)
        self.factor.setRange(0.0, 1.0)

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
    signal_filter_changed = Signal(bool, int)
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

class InterferenceFilter(SimpleFilter):
    signal_filter_changed = Signal(bool, int, bool)
    def __init__(self):
        super(InterferenceFilter, self).__init__('Interference Detection')
        self.limitLabel = QLabel('Limit', self)
        self.limit = QSpinBox(self)
        self.limit.setRange(0, 10000)
        self.layout.addWidget(self.limitLabel)
        self.layout.addWidget(self.limit)

        self.useLastValue = QCheckBox('Use Last Value', self)
        self.layout.addWidget(self.useLastValue)

        self.limit.valueChanged.connect(lambda: self.signal_filter_changed.emit(self.checkBox.isChecked(), self.limit.value(), self.useLastValue.isChecked()))
        self.useLastValue.stateChanged.connect(lambda: self.signal_filter_changed.emit(self.checkBox.isChecked(), self.limit.value(), self.useLastValue.isChecked()))
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)

    def __set_active(self, enable: bool):
        self.limit.setEnabled(enable)
        self.limitLabel.setEnabled(enable)
        self.useLastValue.setEnabled(enable)
        self.signal_filter_changed.emit(enable, self.limit.value(), self.useLastValue.isChecked())

class FilterSettings(QGroupBox):
    def __init__(self, parent=None):
        super(FilterSettings, self).__init__('Camera Filters', parent)
        self.layout = QVBoxLayout()
        self.medianFilter = SimpleFilter('Median Filter')
        self.averageFilter = SimpleFilter('Average Filter')
        self.edgeFilter = EdgeFilter()
        self.temporalFilter = TemporalFilter()
        self.interferenceFilter = InterferenceFilter()

        self.layout.addWidget(self.medianFilter)
        self.layout.addWidget(self.averageFilter)
        self.layout.addWidget(self.edgeFilter)
        self.layout.addWidget(self.temporalFilter)
        self.layout.addWidget(self.interferenceFilter)

        self.setLayout(self.layout) 
