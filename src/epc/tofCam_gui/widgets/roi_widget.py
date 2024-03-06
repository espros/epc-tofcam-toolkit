from PySide6 import QtWidgets  
from PySide6.QtWidgets import QSpinBox, QLabel, QGroupBox, QGridLayout
from PySide6.QtCore import Signal

class RoiSettings(QGroupBox):
    signal_roi_changed = Signal(int, int, int, int)
    def __init__(self, width: int, height: int, label='ROI', steps=1):
        super(RoiSettings, self).__init__(label)
        self.roi_width = width
        self.roi_height = height

        self.gridLayout = QGridLayout()
        self.x1 = QSpinBox(self)
        self.y1 = QSpinBox(self)
        self.x2 = QSpinBox(self)
        self.y2 = QSpinBox(self)

        self.x1.setSingleStep(steps)
        self.y1.setSingleStep(steps)
        self.x2.setSingleStep(steps)
        self.y2.setSingleStep(steps)

        self.x1.setMinimum(0)
        self.x1.setMaximum(width)
        self.y1.setMinimum(0)
        self.y1.setMaximum(height)
        self.x2.setMinimum(0)
        self.x2.setMaximum(width)
        self.y2.setMinimum(0)
        self.y2.setMaximum(height)

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

        self.x1.valueChanged.connect(self.roiChanged)
        self.y1.valueChanged.connect(self.roiChanged)
        self.x2.valueChanged.connect(self.roiChanged)
        self.y2.valueChanged.connect(self.roiChanged)

        self.setLayout(self.gridLayout)

    def roiChanged(self):
        self.x1.setRange(0, self.x2.value()-1)
        self.y1.setRange(0, self.y2.value()-1)
        self.x2.setRange(self.x1.value()+1, self.roi_width)
        self.y2.setRange(self.y1.value()+1, self.roi_height)
        self.signal_roi_changed.emit(self.x1.value(), self.y1.value(), self.x2.value(), self.y2.value())

    def setDefaultValue(self):
        self.x1.setValue(0)
        self.x2.setValue(self.roi_width)
        self.y1.setValue(0)
        self.y2.setValue(self.roi_height)
        self.signal_roi_changed.emit(self.x1.value(), self.y1.value(), self.x2.value(), self.y2.value())
