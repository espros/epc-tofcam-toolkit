import importlib.resources

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICONS = importlib.resources.files('epc.tofCam_gui.icons')


def svg2icon(name: str, size: QSize = QSize(24, 24)) -> QIcon:
    """Render an SVG string to an icon

    Args:
        svg2icon (str): The name of the icon (should be inside the icons location)
        size (QSize, optional): Resulting size. Defaults to QSize(24,24).

    Returns:
        QIcon: The icon to use in buttons
    """
    if not name.endswith(".svg"):
        raise ValueError("The icon name should end with .svg!")
    _filename = ICONS.joinpath(name)
    renderer = QSvgRenderer(str(_filename))  # type: ignore
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)
