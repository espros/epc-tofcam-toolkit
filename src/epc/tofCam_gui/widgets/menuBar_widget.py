from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction


class MenuBar(QMenuBar):
    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent=parent)

        self.fileMenu = QMenu("File", self)
        self.setDefaultValuesAction = QAction("Set default values", self)
        self.fileMenu.addAction(self.setDefaultValuesAction)
        self.savePngAction = QAction("Save png", self)
        self.fileMenu.addAction(self.savePngAction)
        self.saveRawAction = QAction("Save raw", self)
        self.fileMenu.addAction(self.saveRawAction)
        
        self.viewMenu = QMenu("View", self)
        self.openConsoleAction = QAction("Show console", self)
        self.viewMenu.addAction(self.openConsoleAction)

        self.addMenu(self.fileMenu)
        self.addMenu(self.viewMenu)
