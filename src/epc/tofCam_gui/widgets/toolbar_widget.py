import pkg_resources
from PySide6.QtWidgets import QToolBar, QLabel, QWidget, QSizePolicy, QStyle
from PySide6.QtGui import QIcon, QAction


class ToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.gui_version = pkg_resources.get_distribution("epc-tofcam-lib").version
        
        # assemble play button
        self._startIcon = parent.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self._stopIcon = parent.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        self.playButton = QAction(self._startIcon, "Start", self)
        self.playButton.setStatusTip('Start and Stop live Stream')
        self.playButton.setCheckable(True)
        self.playButton.triggered.connect(lambda: self.__setIcon(self.playButton, self._startIcon, self._stopIcon))

        # assemble capture button
        captureIcon = parent.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton)
        self.captureButton = QAction(captureIcon, "Capture", self)
        self.captureButton.setStatusTip('Capture a single frame')
        
        # assemble chip info and fps info
        self.chipInfo = QLabel('Chip ID: 000\nWafer ID: 000')
        self.versionInfo = QLabel(f'GUI: {self.gui_version}\nFW: 000')
        self.fpsInfo = QLabel('FPS: 0')

        # Create the spacers
        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)


        self.addAction(self.playButton)
        self.addAction(self.captureButton)
        self.addWidget(left_spacer)
        self.addWidget(self.versionInfo)
        self.addWidget(self.chipInfo)
        self.addWidget(right_spacer)
        self.addWidget(self.fpsInfo)

    def setFPS(self, fps):
        self.fpsInfo.setText(f'FPS: {fps}')

    def __setIcon(self, button: QAction, on: QIcon, off: QIcon):
        if button.isChecked():
            button.setIcon(off)
        else:
            button.setIcon(on)

    def setVersionInfo(self, fwVersion):
        self.versionInfo.setText(f'GUI: {self.gui_version}\nFW: {fwVersion}')

    def setChipInfo(self, chipID, waferID):
        self.chipInfo.setText(f'Chip ID:  {chipID}\nWafer ID: {waferID}')