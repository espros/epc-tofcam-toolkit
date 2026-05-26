import numpy as np
from scipy.ndimage import convolve, label
import cv2

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
    normImg = curimg / curimg.max()
    normImg *= 255
    normImg = normImg.astype(np.uint8)
    return cv2.Canny(normImg, 100, 50)

class MinAmplitudeFilter():
    def __init__(self, min_amplitude=50):
        self.min_amplitude = min_amplitude

    def filter(self, distance: np.ndarray, amplitude: np.ndarray):
        """
        Filter the distance image based on the amplitude image.
        Pixels with amplitude below the minimum threshold are set to 0 in the distance image.
        """
        filtered_distance = np.copy(distance)
        filtered_distance[amplitude < self.min_amplitude] = 0
        return filtered_distance

class KalmanVideoDenoiser:
    """Pixelwise 1D strong tracking Kalman filter that masks pixels with high uncertainty"""

    def __init__(self, uncertainty_threshold=200, process_noise=100, forgetting_factor=0.5):
        self.uncertainty_threshold = uncertainty_threshold
        self.beta = forgetting_factor
        self.q = process_noise
        self.x = np.array(0)  # estimate image
        self.p = np.array(0)  # estimate variance image
        self.innov_cov_est = np.array(0)  # innovation variance estimate image
        self.initialized = False

    def __call__(self, frame: np.ndarray, amplitude: np.ndarray):
        frame = np.asarray(frame).astype(float)
        amplitude = np.asarray(amplitude).astype(float)

        if not self.initialized:
            self.x = frame
            self.p = np.ones_like(frame)
            self.innov_cov_est = np.ones_like(frame)
            self.initialized = True
            return frame

        innovation = frame - self.x
        r = (22500 / (amplitude + 2.9)) ** 2 # measurement noise estimation from calibration fit

        # standard Kalman "predict" step
        self.p = self.p + self.q

        # forgetting factor beta for innovation covariance estimate (1=never forget)
        self.innov_cov_est = self.beta * self.innov_cov_est + (1 - self.beta) * (innovation ** 2)

        # lambda for boosting Kalman gains in fast-moving pixels (strong tracking filter)
        lam = (self.innov_cov_est - r) / self.p
        lam[lam < 1] = 1 # clip to values > 1
        self.p *= lam

        # Kalman gain
        k = self.p / (self.p + r)

        # standard Kalman "predict" step
        self.x += k * innovation
        self.p *= 1 - k

        # guard against NaN values
        self.x = np.nan_to_num(self.x, nan=frame)
        self.p = np.nan_to_num(self.p, nan=1.0)
        self.innov_cov_est = np.nan_to_num(self.innov_cov_est, nan=1.0)

        # mask pixels with high "uncertainty" (high estimate standard deviation)
        return np.where(np.sqrt(self.p) < self.uncertainty_threshold, self.x, np.nan)


class TemporalFilter:
    "Exponential moving average filter with jump detection"
    
    def __init__(self, alpha=0.2, threshold=300):
        self.alpha = alpha
        self.threshold = threshold
        self.state = np.array(0)

    def __call__(self, frame: np.ndarray):
        diff = frame - self.state
        result = self.alpha * frame + (1-self.alpha) * self.state
        result = np.where(np.abs(diff) < self.threshold, result, frame)
        
        self.state = result
        return result

class EMAFilter:
    "Exponential moving average filter"
    
    def __init__(self, alpha=0.2):
        self.alpha = alpha
        self.state = np.array(np.nan)

    def __call__(self, img: np.ndarray):
        self.state = self.alpha * img + (1 - self.alpha) * self.state
        self.state = np.where(np.isnan(self.state), img, self.state)
        return self.state


def edgeFilter(img: np.ndarray, threshold=300, mask_val=np.nan):
    kernel = np.array([[-1, -1, -1], [-1, +8, -1], [-1, -1, -1]])
    edges = convolve(input=img, weights=kernel, mode='reflect')
    return np.where(np.abs(edges) < threshold, img, mask_val)
