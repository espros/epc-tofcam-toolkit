from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar


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
        self.quitAppAction = QAction("Quit", self)
        self.fileMenu.addAction(self.quitAppAction)


        self.viewMenu = QMenu("View", self)
        self.openConsoleAction = QAction("Show console", self)
        self.viewMenu.addAction(self.openConsoleAction)
        self.toggleFullScreenAction = QAction("Toggle fullscreen", self)
        self.viewMenu.addAction(self.toggleFullScreenAction)

        self.outOfRangeMenu = QMenu("Out of range behaviour", self)
        self.outOfRangeGroup = QActionGroup(self)
        self.outOfRangeClipAction = QAction("Clip", self)
        self.outOfRangeClipAction.setCheckable(True)
        self.outOfRangeZeroAction = QAction("Zero", self)
        self.outOfRangeZeroAction.setCheckable(True)
        self.outOfRangeZeroAction.setChecked(True)
        self.outOfRangeAutoAction = QAction("Autorange", self)
        self.outOfRangeAutoAction.setCheckable(True)
        self.outOfRangeGroup.addAction(self.outOfRangeClipAction)
        self.outOfRangeGroup.addAction(self.outOfRangeZeroAction)
        self.outOfRangeGroup.addAction(self.outOfRangeAutoAction)
        self.outOfRangeMenu.addAction(self.outOfRangeClipAction)
        self.outOfRangeMenu.addAction(self.outOfRangeZeroAction)
        self.outOfRangeMenu.addAction(self.outOfRangeAutoAction)
        self.viewMenu.addMenu(self.outOfRangeMenu)

        self.unitsMenu = QMenu("Units", self)
        self.unitsGroup = QActionGroup(self)
        self.unitsMmAction = QAction("mm", self)
        self.unitsMmAction.setCheckable(True)
        self.unitsMmAction.setChecked(True)
        self.unitsCmAction = QAction("cm", self)
        self.unitsCmAction.setCheckable(True)
        self.unitsInchesAction = QAction("Inches", self)
        self.unitsInchesAction.setCheckable(True)
        self.unitsGroup.addAction(self.unitsMmAction)
        self.unitsGroup.addAction(self.unitsCmAction)
        self.unitsGroup.addAction(self.unitsInchesAction)
        self.unitsMenu.addAction(self.unitsMmAction)
        self.unitsMenu.addAction(self.unitsCmAction)
        self.unitsMenu.addAction(self.unitsInchesAction)
        self.viewMenu.addMenu(self.unitsMenu)

        self.quitAppAction.setShortcut(QKeySequence("Ctrl+q"))
        self.toggleFullScreenAction.setShortcut(QKeySequence("Ctrl+f"))

        self.addMenu(self.fileMenu)
        self.addMenu(self.viewMenu)
