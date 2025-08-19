import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt

chessBoard = np.loadtxt('tmp/Amplitude_ChessBoard.csv', delimiter=',')

# rotate 90 degrees
chessBoard = np.rot90(chessBoard, k=1)
chessBoard /= chessBoard.max()
# chessBoard[chessBoard > 0.1] = 0.1
# chessBoard *= 10
chessBoard = (chessBoard * 255).astype(np.uint8)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*9,3), np.float32)
objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)

ret, corners = cv2.findChessboardCorners(chessBoard, (9,6), flags=cv2.CALIB_USE_INTRINSIC_GUESS)
print(ret, corners.shape)

imgpoints = cv2.cornerSubPix(chessBoard, corners, (11,11), (-1,-1), criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
rgb = cv2.cvtColor(chessBoard, cv2.COLOR_GRAY2RGB)
cv2.drawChessboardCorners(rgb, (9,6), corners, ret)

ret, mxt, dist, rvecs, tvecs = cv2.calibrateCamera([objp], [imgpoints], chessBoard.shape[::-1], None, None)
print(ret, mxt, dist, rvecs, tvecs)

h, w = rgb.shape[:2]
newcamera, roi = cv2.getOptimalNewCameraMatrix(mxt, dist, (w,h), 1.0, (w,h))
result = cv2.undistort(chessBoard, mxt, dist, None, None)

cv2.imshow('chessBoard', result)
cv2.waitKey(0)
cv2.destroyAllWindows()
# plt.imshow(chessBoard, vmin=0, vmax=255, cmap='gray')
# plt.show()