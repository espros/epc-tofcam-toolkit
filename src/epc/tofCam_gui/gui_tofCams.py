import time
from PySide6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QWidget
from epc.tofCam_gui.widgets import VideoWidget, ToolBar

class Base_GUI_TOFcam(QMainWindow):
    def __init__(self, title: str, parent=None):
        super(Base_GUI_TOFcam, self).__init__()
        self.setWindowTitle(title)

        self.time_last_frame = time.time()
        self.__filter_cb = None

        # create main widgets
        self.toolBar = ToolBar(self)
        self.imageView = VideoWidget()
        self.settingsLayout = QVBoxLayout()
        self.mainLayout = QGridLayout()
        self.widget = QWidget()

        self.addToolBar(self.toolBar)

    def setFilter_cb(self, filter_cb):
        self.__filter_cb = filter_cb

    def updateImage(self, image):
        time_diff = time.time() - self.time_last_frame
        if time_diff != 0:
            fps = round(1 / time_diff)
            self.toolBar.setFPS(fps)

        self.time_last_frame = time.time()
        if self.__filter_cb:
            image = self.__filter_cb(image)
        self.imageView.setImage(image, autoRange=False, autoHistogramRange=False, autoLevels=False)

    def complete_setup(self):
        """ ! needs to be called at the end of the __init__ method of the derived class !
        """
        self.mainLayout.setSpacing(10)
        self.mainLayout.addLayout(self.settingsLayout, 0, 0)
        self.mainLayout.addWidget(self.imageView, 0, 1)
        self.mainLayout.setColumnStretch(1, 3)

        self.widget.setLayout(self.mainLayout)  
        self.setCentralWidget(self.widget)

        self.resize(1200, 600)

