import importlib.metadata
import importlib.resources

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolBar, QWidget

from epc.tofCam_gui.icon_svg import svg2icon

_LOGO_PATH = importlib.resources.files(
    'epc.tofCam_gui.icons').joinpath('epc-logo.png')


class ToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui_version = importlib.metadata.version("epc-tofcam-toolkit")

        # Render icons at run-time
        self._icons = {_name: svg2icon(f"{_name}.svg")
                       for _name in ["play", "stop", "capture", "record", "file_import"]}

        # Buttons
        self.playButton = QAction(
            self._icons["play"], "Start", self, toolTip="Start and stop live stream", checkable=True)
        self.captureButton = QAction(
            self._icons["capture"], "Capture", self, toolTip="Capture a single frame")
        self.recordButton = QAction(
            self._icons["record"], "Record", self, toolTip="Record live stream", checkable=True)
        self.importButton = QAction(
            self._icons["file_import"], "Import File", self, toolTip="Import a file to replay", checkable=True)

        # Button actions
        self.playButton.toggled.connect(self._playButtonToggled)
        self.recordButton.toggled.connect(self._recordButtonToggled)
        self.importButton.toggled.connect(self._importButtonToggled)

        # Chip and fps info
        self.chipInfo = QLabel('Chip ID: 000\nWafer ID: 000')
        self.versionInfo = QLabel(f'GUI: {self.gui_version}\nFW: 000')
        self.fpsInfo = QLabel('FPS: 0')
        self.fpsInfo.setFont(QFont("monospace"))

        # Logo
        esprosLogo = QPixmap(_LOGO_PATH)  # type: ignore
        esprosLogo = esprosLogo.scaled(
            100, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo = QLabel(pixmap=esprosLogo,
                           alignment=Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(100, 50)

        # Create the spacers
        left_spacer = QWidget()
        left_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_spacer = QWidget()
        right_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.addAction(self.playButton)
        self.addAction(self.captureButton)
        self.addAction(self.recordButton)
        self.addAction(self.importButton)

        self.addWidget(left_spacer)
        self.addWidget(self.versionInfo)
        self.addWidget(self.chipInfo)
        self.addWidget(right_spacer)
        self.addWidget(self.fpsInfo)
        self.addWidget(self.logo)

    def setFPS(self, fps) -> None:
        self.fpsInfo.setText(f'FPS: {fps:5.1f}')

    def _playButtonToggled(self) -> None:
        self.__setOnOffIcons(
            self.playButton, self._icons["play"], self._icons["stop"])

        if not self.playButton.isChecked() and self.recordButton.isChecked():
            QTimer.singleShot(0, self.recordButton.trigger)

        self.captureButton.setEnabled(not self.playButton.isChecked())

    def _recordButtonToggled(self) -> None:
        if self.recordButton.isChecked() and not self.playButton.isChecked():
            QTimer.singleShot(0, self.playButton.trigger)

    def _importButtonToggled(self) -> None:
        if self.playButton.isChecked():
            QTimer.singleShot(0, self.playButton.trigger)

    def __setOnOffIcons(self, button: QAction, on: QIcon, off: QIcon) -> None:
        """Set ON/OFF icon variations for the same button

        Args:
            button (QAction): The button to set the icons
            on (QIcon): ON icon
            off (QIcon): OFF icon
        """
        if button.isChecked():
            button.setIcon(off)
        else:
            button.setIcon(on)

    def setVersionInfo(self, fwVersion: str) -> None:
        self.versionInfo.setText(f'GUI: {self.gui_version}\nFW: {fwVersion}')

    def setChipInfo(self, chipID: int, waferID: int) -> None:
        self.chipId = chipID
        self.waferId = waferID
        self.chipInfo.setText(f'Chip ID:  {chipID}\nWafer ID: {waferID}')
