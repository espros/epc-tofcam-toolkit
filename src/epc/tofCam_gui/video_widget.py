from PyQt5.QtWidgets import QWidget
from pyqtgraph import ImageView, ColorMap
import numpy as np

CMAP_DISTANCE = [   (  0,   0,   0),
                    (255,   0,   0),
                    (255, 255,   0),
                    (  0, 255,   0),
                    (  0, 240, 240),
                    (  0,   0, 255),
                    (255,   0, 255)]

CMAP_GRAYSCALE =  [ (0, 0, 0),
                    (51, 51, 51),
                    (102, 102, 102),
                    (153, 153, 153),
                    (204, 204, 204),
                    (255, 255, 255)]

class VideoWidget(ImageView):
    GRAYSCALE_CMAP = ColorMap(pos=np.linspace(0.0, 1.0, 6), color=CMAP_GRAYSCALE)
    DISTANCE_CMAP = ColorMap(pos=np.linspace(0.0, 1.0, 6), color=CMAP_DISTANCE)

    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.cmap = CMAP_DISTANCE

    def __set_cmap(self, cmap):
        if not self.cmap == cmap:
            self.cmap = cmap
            self.setColorMap(self.cmap)

    def updateGrsc(self, image: np.ndarray):
        self.__set_cmap(CMAP_GRAYSCALE)
        self.setImage(image, autoRange=False, autoLevels=False, autoHistogramRange=False, levels=(0, 255), lut=self.cmap)

    def updateAmp(self, image: np.ndarray):
        self.__set_cmap(CMAP_DISTANCE)
        self.setImage(image, autoRange=False, autoLevels=False, autoHistogramRange=False, levels=(0, 255), lut=self.cmap)

    def updateDistance(self, image: np.ndarray):
        self.__set_cmap(CMAP_DISTANCE)
        self.setImage(image, autoRange=False, autoLevels=False, autoHistogramRange=False, levels=(0, 255), lut=self.cmap)

