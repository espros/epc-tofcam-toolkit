import sys
import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
from scipy.ndimage import convolve, label
import cv2


from pyqtgraph.Qt import  QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton
from pyqtgraph.functions import Colors

sys.path.append('.')
from epc.tofCam660.productfactory import ProductFactory
from epc.tofCam660.server import Server

def gradimg (curimg):
    gaussian= gaussian_filter(9, 1.4)
    PrewittX = convolve(gaussian, np.array([[1, 0, -1]]).T)
    PrewittY = convolve(gaussian, np.array([[1, 0, -1]]))
    g_x = convolve(curimg, PrewittX)
    g_y = convolve(curimg, PrewittY)
    return np.sqrt(g_x ** 2 + g_y ** 2)*2

def gaussian_filter(size, sigma):
    x, y = np.mgrid[-size // 2 + 1:size // 2 + 1, -size // 2 + 1:size // 2 + 1]
    g = np.exp(-((x ** 2 + y ** 2) / (2.0 * sigma ** 2)))
    return g / g.sum()

def threshgrad(curimg,highsens=200,lowsens=100):#DEFAULT 8,2 FOR GREYSCALE IMAGES 254,160 FOR DISTANCE

    gaussian= gaussian_filter(9, 1.4)
    PrewittX = convolve(gaussian, np.array([[1, 0, -1]]).T)
    PrewittY = convolve(gaussian, np.array([[1, 0, -1]]))
    g_x = convolve(curimg, PrewittX)
    g_y = convolve(curimg, PrewittY)
    LowPass = np.zeros(shape=curimg.shape, dtype=np.int16)
    thresholded = np.zeros(shape=curimg.shape, dtype=np.int16)
    LowPass[curimg > lowsens ]= 1
    OneBlock = np.ones(shape=(3,3))
    BlocksMarked, NumberOfLabels = label(LowPass, OneBlock)
    thresholded[np.isin(BlocksMarked, list(set(BlocksMarked[curimg > highsens])))] = 255
    return thresholded


def cannyE (curimg):
    return cv2.Canny
