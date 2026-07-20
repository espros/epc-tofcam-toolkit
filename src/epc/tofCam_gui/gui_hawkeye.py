import sys
import threading
import qdarktheme
from typing import TYPE_CHECKING, Any
from PySide6 import QtWidgets
from PySide6.QtWidgets import QSpinBox
from PySide6.QtGui import QValidator, QFocusEvent
from PySide6.QtWidgets import QSpinBox, QLabel, QGroupBox, QGridLayout
from PySide6.QtCore import Signal
from epc.tofCam_gui import Base_GUI_TOFcam
from epc.tofCam_gui.widgets import (VideoWidget,
                                    GroupBoxSelection,
                                    DropDownSetting,
                                    SettingsGroup,
                                    IntegrationTimes,
                                    SpinBoxSetting)
from epc.tofCam_gui.widgets.filter_widgets import (EdgeFilter,
                                                   SimpleFilter,
                                                   TemporalFilter)
if TYPE_CHECKING:
    # Import the actual class here just for Mypy's sake
    from epc.tofCam_lib.tofCam import TOFcam


class ParitySpinBox(QSpinBox):
    def __init__(self, *args, is_even=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_even = is_even
        
        # Set a function to check if a number matches our rule
        # If is_even is True, looks for num % 2 == 0. If False, looks for num % 2 != 0.
        self.is_valid_parity = lambda num: (num % 2 == 0) if self.is_even else (num % 2 != 0)
        
        # Initialize to a valid starting number based on selection
        initial_value = 0 if self.is_even else 1
        self.setValue(initial_value)
        self.setSingleStep(2)
        self.setKeyboardTracking(False)
        
        # Track history for the snap-back feature
        self.last_valid_value = self.value()
        self.valueChanged.connect(self.store_valid_value)

    def store_valid_value(self, val):
        if self.is_valid_parity(val):
            self.last_valid_value = val

    def stepBy(self, steps):
        super().stepBy(steps)
        if not self.is_valid_parity(self.value()):
            # Push it forward or backward by 1 to fix alignment if it breaks
            self.setValue(self.value() + (1 if steps > 0 else -1))

    def validate(self, text, pos):
        if not text or text == "-":
            return QValidator.State.Intermediate, text, pos
        try:
            num = int(text)
            if self.is_valid_parity(num):
                return QValidator.State.Acceptable, text, pos
            else:
                return QValidator.State.Intermediate, text, pos
        except ValueError:
            return QValidator.State.Invalid, text, pos

    def focusOutEvent(self, event: QFocusEvent):
        try:
            num = int(self.text())
            if not self.is_valid_parity(num):
                self.setValue(self.last_valid_value)
        except ValueError:
            self.setValue(self.last_valid_value)
        super().focusOutEvent(event)


class RoiSettingsHawkeye(QGroupBox):
    signal_roi_changed = Signal(int, int, int, int)

    def __init__(self, width: int, height: int, label='ROI', defaults=None, max_span_x: int = 60, max_span_y: int = 60):
        super(RoiSettingsHawkeye, self).__init__(label)
        self.roi_width = width
        self.roi_height = height
        self.steps = 2
        self.last_roi_values = (0, 0, width, height)
        self.defaults = defaults
        self.max_span_x = max_span_x
        self.max_span_y = max_span_y
        self.roi_change_lock = threading.Lock()

        self.gridLayout = QGridLayout()
        self.x1 = ParitySpinBox(self, is_even=True)
        self.y1 = ParitySpinBox(self, is_even=True)
        self.x2 = ParitySpinBox(self, is_even=False)
        self.y2 = ParitySpinBox(self, is_even=False)

        self.x1.setRange(0, width - 1)
        self.y1.setRange(0, height - 1)
        self.x2.setRange(1, width)
        self.y2.setRange(1, height)

        self.x1.setValue(0)
        self.y1.setValue(0)
        self.x2.setValue(width)
        self.y2.setValue(height)

        self.x1Label = QLabel('X1', self)
        self.y1Label = QLabel('Y1', self)
        self.x2Label = QLabel('X2', self)
        self.y2Label = QLabel('Y2', self)

        self.gridLayout.addWidget(self.x1Label, 0, 0)
        self.gridLayout.addWidget(self.x1, 0, 1)
        self.gridLayout.addWidget(self.y1Label, 1, 0)
        self.gridLayout.addWidget(self.y1, 1, 1)
        self.gridLayout.addWidget(self.x2Label, 0, 2)
        self.gridLayout.addWidget(self.x2, 0, 3)
        self.gridLayout.addWidget(self.y2Label, 1, 2)
        self.gridLayout.addWidget(self.y2, 1, 3)

        self.setLayout(self.gridLayout)

        for spinbox in [self.x1, self.y1, self.x2, self.y2]:
            spinbox.valueChanged.connect(self.roiChanged)

    def roiChanged(self):
        """ Overwrite the roiChanged method to make sure total width or height is always below 60 pixels. """
        if self.roi_change_lock.acquire(blocking=False):
            try:
                sender = self.sender()
                match sender:
                    case self.y1:
                        y2_max = self.y1.value() + self.max_span_y - 1
                        if self.y2.value() > y2_max:
                            self.y2.setRange(1, self.roi_height) # temporarilly set range to max
                            self.y2.setValue(y2_max)
                    case self.y2:
                        y1_min = self.y2.value() - self.max_span_y + 1
                        if self.y1.value() < y1_min:
                            self.y1.setRange(0, self.roi_height - 1) # temporarilly set range to max
                            self.y1.setValue(y1_min)
                    case self.x1:
                        x2_max = self.x1.value() + self.max_span_x - 1
                        if self.x2.value() > x2_max:
                            self.x2.setRange(1, self.roi_width) # temporarilly set range to max
                            self.x2.setValue(x2_max)
                    case self.x2:
                        x1_min = self.x2.value() - self.max_span_x + 1
                        if self.x1.value() < x1_min:
                            self.x1.setRange(0, self.roi_width - 1) # temporarilly set range to max
                            self.x1.setValue(x1_min)                

                # reset ranges
                self.x1.setRange(0, self.x2.value() - 1)
                self.y1.setRange(0, self.y2.value() - 1)
                self.x2.setRange(self.x1.value() + 1, self.roi_width)
                self.y2.setRange(self.y1.value() + 1, self.roi_height)

                # emit signal only if roi values are changed
                current_values = (self.x1.value(), self.y1.value(),
                                self.x2.value(), self.y2.value())
                if current_values != self.last_roi_values:
                    self.signal_roi_changed.emit(*current_values)
                    self.last_roi_values = current_values
            finally:
                self.roi_change_lock.release()

    def setDefaultValue(self):
        if self.defaults:
            self.x1.setValue(self.defaults[0])
            self.x2.setValue(self.defaults[2])
            self.y1.setValue(self.defaults[1])
            self.y2.setValue(self.defaults[3])
        else:
            self.x1.setValue(0)
            self.x2.setValue(self.roi_width)
            self.y1.setValue(0)
            self.y2.setValue(self.roi_height)
        self.signal_roi_changed.emit(
            self.x1.value(), self.y1.value(), self.x2.value(), self.y2.value())


class GUI_Hawkeye(Base_GUI_TOFcam):
    def __init__(self, title='GUI-Hawkeye', parent=None):
        super(GUI_Hawkeye, self).__init__(title)

        # Create the video widget
        self.imageView = VideoWidget()
        self.imageTypeWidget = GroupBoxSelection('Image Type', ['Distance', 'Amplitude', 'Grayscale'])
        self.integrationTimes = IntegrationTimes(['TOF'], defaults=[100], limits=[4000], min_value=1)
        self.integrationTimes.autoMode.setVisible(False)
        self.minAmplitude = SpinBoxSetting('Minimal Amplitude', 0, 1000, default=50)
        self.modulationFrequency = DropDownSetting('Modulation Frequency', ['20 MHz', '10 MHz'], default='10 MHz')
        self.modeSettings = SettingsGroup('Camera Modes', [self.modulationFrequency])
        self.roiSettings = RoiSettingsHawkeye(159, 59, defaults=(50,0,109,59), max_span_x=60, max_span_y=60)

        # Filters        
        self.medianFilter = SimpleFilter('Median Filter')
        self.averageFilter = SimpleFilter('Average Filter')
        self.edgeFilter = EdgeFilter(range=(0, 5000), threshold=300)
        self.temporalFilter = TemporalFilter()
        # turn off edge detection for now:
        self.builtInFilter = SettingsGroup('Image Filters', [self.medianFilter, self.averageFilter, self.temporalFilter])
        # self.builtInFilter = SettingsGroup('Image Filters', [self.medianFilter, self.averageFilter, self.edgeFilter, self.temporalFilter])
        
        # Tool Tips
        withLimit = '<div style="max-width: 200px;">'
        self.imageTypeWidget.setToolTip(
            withLimit + 'Select the type of image to display.</div>')
        self.modulationFrequency.setToolTip(
            withLimit + 'Set the modulation frequency of the camera. Higher frequencies '
            'can provide better resolution but lower maximal range.</div>')
        self.integrationTimes.setToolTip(
            withLimit + 'Set the integration times. Grayscale uses the same value.</div>')
        self.minAmplitude.setToolTip(
            withLimit + 'Set the minimal amplitude threshold. Pixels with an amplitude '
            'below this value will be ignored in the distance calculation.</div>')
        self.medianFilter.checkBox.setToolTip(
            withLimit + 'Apply a median filter to the image. '
            'This can help reduce noise and improve image quality.</div>')
        self.averageFilter.checkBox.setToolTip(
            withLimit + 'Apply an average filter to the image. '
            'This can help reduce noise but may also blur the image.</div>')
        self.edgeFilter.checkBox.setToolTip(
            withLimit + 'Apply an edge filter to the image. '
            'This can reduce floating pixels at sharp edges.</div>')
        self.temporalFilter.checkBox.setToolTip(
            withLimit + 'Apply a temporal filter to the image. '
            'This can help reduce noise by averaging over multiple frames.</div>')

        #Create Layout for settings
        self.settingsLayout.addWidget(self.imageTypeWidget)
        self.settingsLayout.addWidget(self.modeSettings)
        self.settingsLayout.addWidget(self.integrationTimes)
        self.settingsLayout.addWidget(self.minAmplitude)
        self.settingsLayout.addWidget(self.builtInFilter)
        # hide for now:
        #self.settingsLayout.addWidget(self.roiSettings)

        self.complete_setup()

    def _set_bridge(self, cam:"TOFcam", *args: Any, **kwargs: Any) -> None:
        from epc.tofCam_gui.gui_hawkeye_bridge import Hawkeye_bridge
        super()._set_bridge(cam=cam, _bridge_type=Hawkeye_bridge)


def main():
    app = QtWidgets.QApplication(sys.argv)

    qdarktheme.setup_theme()
    stream = GUI_Hawkeye()
    stream.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()