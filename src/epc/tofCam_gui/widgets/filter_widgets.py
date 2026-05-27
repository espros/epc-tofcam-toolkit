from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QSpinBox, QDoubleSpinBox, QGroupBox, QVBoxLayout, QSlider
from PySide6.QtCore import Signal, Qt

TOOL_TIP_WIDTH = '<div style="max-width: 200px;">'

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

        self.threshold.setToolTip(
            TOOL_TIP_WIDTH + 'Set the distance threshold for the temporal filter. '
            'If the distance of a pixel changes by more than this threshold compared to the '
            'previous frame, the filter will be reset for this pixel.</div>')
        self.factor.setToolTip(
            TOOL_TIP_WIDTH + 'Set the blending factor for the temporal filter. '
            'A value of 0 means that only the current frame is used, while a value of 1 means '
            'that only the averaged frames are used. Values in between will blend the current '
            'and averaged frames accordingly.</div>')

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
        self.threshold.setToolTip(
            TOOL_TIP_WIDTH + 'Pixels whose distance differs from a neighboring pixel '
            'by more than this threshold are considered edges and will be filtered out.</div>')

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

        self.limit.setToolTip(
            TOOL_TIP_WIDTH + 'Set the interference amplitude threshold '
            'for interference detection.</div>')
        self.useLastValue.setToolTip(
            TOOL_TIP_WIDTH + 'If enabled, the last valid value will be used for pixels '
            'detected as interference. Otherwise, they will be marked as invalid.</div>')

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

class KalmanFilter(SimpleFilter):
    signal_filter_changed = Signal(bool, float)
    def __init__(self, name='Kalman Filter', default_value=200.0, default_on=False):
        super(KalmanFilter, self).__init__(name, default_on)

        self.slider_default = default_value
        self.default_on = default_on

        self.label = QLabel('Max. Uncertainty [mm]', self)
        self.slider = QSlider(Qt.Horizontal, self)
        self.sbox = QSpinBox(self)
        self.slider.setRange(10, 200)
        self.sbox.setRange(10, 200)
        self.slider.setValue(self.slider_default)
        self.sbox.setValue(self.slider_default)

        self.sbox.setToolTip(
            TOOL_TIP_WIDTH + 'Set the maximum uncertainty for the Kalman filter. '
            'Higher values will make the filter more responsive to changes but may also '
            'let through more noise.</div>')

        layout = self.layout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.sbox)

        self.sbox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.sbox.setValue)
        self.slider.valueChanged.connect(lambda: self.__emit_signal())
        self.checkBox.stateChanged.disconnect()
        self.checkBox.stateChanged.connect(self.__set_active)
        self.__set_active(False)

    def isChecked(self) -> bool:
        return self.checkBox.isChecked()

    def __emit_signal(self):
        self.signal_filter_changed.emit(self.checkBox.isChecked(), self.slider.value())

    def __set_active(self, enable: bool):
        self.label.setEnabled(enable)
        self.slider.setEnabled(enable)
        self.sbox.setEnabled(enable)
        self.signal_filter_changed.emit(enable, self.slider.value())

    def setDefaultValue(self):
        self.checkBox.setChecked(self.default_on)
        self.slider.setValue(self.slider_default)
        self.__emit_signal()
