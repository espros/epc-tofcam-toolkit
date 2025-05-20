import importlib.metadata
import importlib.resources

from PySide6.QtCore import QByteArray, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QFont, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolBar, QWidget


def _svg2icon(svg_string: str, size: QSize = QSize(24, 24)) -> QIcon:
    """Render an SVG string to an icon

    Args:
        svg_string (str): The string to render
        size (QSize, optional): Resulting size. Defaults to QSize(24,24).

    Returns:
        QIcon: _description_
    """
    renderer = QSvgRenderer(QByteArray(svg_string.encode("utf-8")))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


# Collection of svg strings to render button icons
# https://tabler.io/icons
_SVG_DICT = {
    "play": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#4CAF50"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-play"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M6 4v16a1 1 0 0 0 1.524 .852l13 -8a1 1 0 0 0 0 -1.704l-13 -8a1 1 0 0 0 -1.524 .852z" /></svg>""",
    "pause": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#7986CB"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-pause"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 4h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h2a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2z" /><path d="M17 4h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h2a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2z" /></svg>""",
    "stop": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#F44336"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-stop"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M17 4h-10a3 3 0 0 0 -3 3v10a3 3 0 0 0 3 3h10a3 3 0 0 0 3 -3v-10a3 3 0 0 0 -3 -3z" /></svg>""",
    "capture": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#03A9F4"  class="icon icon-tabler icons-tabler-filled icon-tabler-capture"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M8 3a1 1 0 0 1 .117 1.993l-.117 .007h-2a1 1 0 0 0 -.993 .883l-.007 .117v2a1 1 0 0 1 -1.993 .117l-.007 -.117v-2a3 3 0 0 1 2.824 -2.995l.176 -.005h2z" /><path d="M4 15a1 1 0 0 1 .993 .883l.007 .117v2a1 1 0 0 0 .883 .993l.117 .007h2a1 1 0 0 1 .117 1.993l-.117 .007h-2a3 3 0 0 1 -2.995 -2.824l-.005 -.176v-2a1 1 0 0 1 1 -1z" /><path d="M18 3a3 3 0 0 1 2.995 2.824l.005 .176v2a1 1 0 0 1 -1.993 .117l-.007 -.117v-2a1 1 0 0 0 -.883 -.993l-.117 -.007h-2a1 1 0 0 1 -.117 -1.993l.117 -.007h2z" /><path d="M20 15a1 1 0 0 1 .993 .883l.007 .117v2a3 3 0 0 1 -2.824 2.995l-.176 .005h-2a1 1 0 0 1 -.117 -1.993l.117 -.007h2a1 1 0 0 0 .993 -.883l.007 -.117v-2a1 1 0 0 1 1 -1z" /><path d="M12 8a4 4 0 1 1 -3.995 4.2l-.005 -.2l.005 -.2a4 4 0 0 1 3.995 -3.8z" /></svg>""",
    "record": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#D32F2F"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-record"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M8 5.072a8 8 0 1 1 -3.995 7.213l-.005 -.285l.005 -.285a8 8 0 0 1 3.995 -6.643z" /></svg>""",
    "file_import": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-file-import"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M5 13v-8a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2h-5.5m-9.5 -2h7m-3 -3l3 3l-3 3" /></svg>""",
    "replay": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#388E3C"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-track-next"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M2 5v14c0 .86 1.012 1.318 1.659 .753l8 -7a1 1 0 0 0 0 -1.506l-8 -7c-.647 -.565 -1.659 -.106 -1.659 .753z" /><path d="M13 5v14c0 .86 1.012 1.318 1.659 .753l8 -7a1 1 0 0 0 0 -1.506l-8 -7c-.647 -.565 -1.659 -.106 -1.659 .753z" /></svg>""",
    "step_back": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#9E9E9E"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-skip-back"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M19.496 4.136l-12 7a1 1 0 0 0 0 1.728l12 7a1 1 0 0 0 1.504 -.864v-14a1 1 0 0 0 -1.504 -.864z" /><path d="M4 4a1 1 0 0 1 .993 .883l.007 .117v14a1 1 0 0 1 -1.993 .117l-.007 -.117v-14a1 1 0 0 1 1 -1z" /></svg>""",
    "step_forward": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="#9E9E9E"  class="icon icon-tabler icons-tabler-filled icon-tabler-player-skip-forward"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 5v14a1 1 0 0 0 1.504 .864l12 -7a1 1 0 0 0 0 -1.728l-12 -7a1 1 0 0 0 -1.504 .864z" /><path d="M20 4a1 1 0 0 1 .993 .883l.007 .117v14a1 1 0 0 1 -1.993 .117l-.007 -.117v-14a1 1 0 0 1 1 -1z" /></svg>""",
    "wifi": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-wifi"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 18l.01 0" /><path d="M9.172 15.172a4 4 0 0 1 5.656 0" /><path d="M6.343 12.343a8 8 0 0 1 11.314 0" /><path d="M3.515 9.515c4.686 -4.687 12.284 -4.687 17 0" /></svg>""",
    "wifi_off": """<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-wifi-off"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 18l.01 0" /><path d="M9.172 15.172a4 4 0 0 1 5.656 0" /><path d="M6.343 12.343a7.963 7.963 0 0 1 3.864 -2.14m4.163 .155a7.965 7.965 0 0 1 3.287 2" /><path d="M3.515 9.515a12 12 0 0 1 3.544 -2.455m3.101 -.92a12 12 0 0 1 10.325 3.374" /><path d="M3 3l18 18" /></svg>"""
}
_LOGO_PATH = importlib.resources.files('epc.tofCam_gui.icons').joinpath('epc-logo.png')


class ToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui_version = importlib.metadata.version("epc-tofcam-toolkit")

        # Render icons at run-time
        self._icons = {_key: _svg2icon(_val) for _key, _val in _SVG_DICT.items()}

        # Buttons
        self.playButton = QAction(self._icons["play"], "Start", self, toolTip="Start and stop live stream", checkable=True)
        self.captureButton = QAction(self._icons["capture"], "Capture", self, toolTip="Capture a single frame")
        self.recordButton = QAction(self._icons["record"], "Record", self, toolTip="Record live stream", checkable=True)
        self.importButton = QAction(self._icons["file_import"], "Import File", self, toolTip="Import a file to replay", checkable=True)
        self.replayButton = QAction(self._icons["replay"], "Replay", self, toolTip="Replay the recorded stream", checkable=True, enabled=False)

        # Button actions
        self.playButton.toggled.connect(self._playButtonToggled)
        self.recordButton.toggled.connect(self._recordButtonToggled)
        self.importButton.toggled.connect(self._importButtonToggled)
        self.replayButton.toggled.connect(self._replayButtonToggled)

        # Chip and fps info
        self.chipInfo = QLabel('Chip ID: 000\nWafer ID: 000')
        self.versionInfo = QLabel(f'GUI: {self.gui_version}\nFW: 000')
        self.fpsInfo = QLabel('FPS: 0')
        self.fpsInfo.setFont(QFont("monospace"))

        # Logo
        esprosLogo = QPixmap(_LOGO_PATH)  # type: ignore
        esprosLogo = esprosLogo.scaled(
            100, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo = QLabel(pixmap=esprosLogo, alignment=Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(100, 50)

        # Create the spacers
        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.addAction(self.playButton)
        self.addAction(self.captureButton)
        self.addAction(self.recordButton)
        self.addAction(self.importButton)
        self.addAction(self.replayButton)

        self.addWidget(left_spacer)
        self.addWidget(self.versionInfo)
        self.addWidget(self.chipInfo)
        self.addWidget(right_spacer)
        self.addWidget(self.fpsInfo)
        self.addWidget(self.logo)

    def setFPS(self, fps) -> None:
        self.fpsInfo.setText(f'FPS: {fps:5.1f}')

    def _playButtonToggled(self) -> None:
        self.__setOnOffIcons(self.playButton, self._icons["play"], self._icons["stop"])

        if not self.playButton.isChecked() and self.recordButton.isChecked():
            QTimer.singleShot(0, self.recordButton.trigger)

        self.captureButton.setEnabled(not self.playButton.isChecked())

    def _recordButtonToggled(self) -> None:
        if self.recordButton.isChecked() and not self.playButton.isChecked():
            QTimer.singleShot(0, self.playButton.trigger)

    def _importButtonToggled(self) -> None:
        if self.playButton.isChecked():
            QTimer.singleShot(0, self.playButton.trigger)

        QTimer.singleShot(100, lambda: self.playButton.setEnabled(not self.importButton.isChecked()))
        QTimer.singleShot(100, lambda: self.captureButton.setEnabled(not self.importButton.isChecked()))
        QTimer.singleShot(100, lambda: self.recordButton.setEnabled(not self.importButton.isChecked()))

        QTimer.singleShot(100, lambda: self.replayButton.setEnabled(self.importButton.isChecked()))

    def _replayButtonToggled(self) -> None:
        self.__setOnOffIcons(self.replayButton, self._icons["replay"], self._icons["pause"])

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

    def setVersionInfo(self, fwVersion: int) -> None:
        self.versionInfo.setText(f'GUI: {self.gui_version}\nFW: {fwVersion}')

    def setChipInfo(self, chipID: int, waferID: int) -> None:
        self.chipId = chipID
        self.waferId = waferID
        self.chipInfo.setText(f'Chip ID:  {chipID}\nWafer ID: {waferID}')
