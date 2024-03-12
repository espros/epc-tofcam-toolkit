##################################################################################################
#
# Copyright 2021 Espros Photonics AG
# Author:            ESPROS RPO,RCS
# Creation:          2021
# Version:           1.0
#
###################################################################################################
# This script does the following:
#
#   Communication between camera (server) and python framework.
#
###################################################################################################

import os
import time
import atexit
import struct
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from epc.tofCam660.command import Command
from epc.tofCam660.parser import GrayscaleParser, DistanceParser, DistanceAndAmplitudeParser, DcsParser
from epc.tofCam660.mac_address_generator import total_random as generateRandomMacAddress
from epc.tofCam660.epc660 import Epc660
from epc.tofCam_lib.transformations_3d import Lense_Projection

colors = [(0, 0, 0),
          (255, 0, 0),
          (255, 255, 0),
          (0, 255, 0),
          (0, 240, 240),
          (0, 0, 255),
          (255, 0, 255)]

class Server:
    def __init__(self, dut: Epc660):
        self.dut = dut
        self.registerAtExits()
        self.maxDepth = 16000 # pixel code limit for valid data 
        self.lensProjection = Lense_Projection.from_lense_calibration('Wide Field')

    def recordVideo(self, frames, folder):
        try:
            os.mkdir(folder)
        except:
            pass
        plt.ion()
        print('recording..')
        for i in range(frames):
            name = '/image' + str(i) + '.bmp'

            curImage = self.getTofAmplitude()[0]
            max = np.amax(curImage)
            curImage = (curImage / max) * 255
            curImage = curImage.astype('uint8')
            img = Image.fromarray(curImage)
            plt.imshow(curImage)
            plt.pause(0.001)
            plt.clf()

            img.save(folder + '/' + name)

        print('recording over')

    def playVideo(self, frames, folder):
        plt.ion()
        print('playing.. ')

        for i in range(frames):
            name = folder + '/image' + str(i) + '.bmp'
            curImage = Image.open(name)
            plt.imshow(curImage)
            plt.pause(0.001)
            plt.clf()
        print('video over')

    def registerAtExits(self):
        atexit.register(self.shutdown)


    def transceive(self, command):
        return self.dut.transceive(command).data

    def writeRegister(self, register, value):
        return self.transceive(Command.create('writeRegister', {'address': register, 'value': value}))

    def readRegister(self, register):
        return self.transceive(Command.create('readRegister', register))

    def waitTillCameraBooted(self):
        self.dut.waitTillCameraBooted()

    def shutdown(self):
        self.dut.shutdown()
        time.sleep(2)

    def getChipId(self):
        return self.transceive(Command.create('readChipInformation'))['chipid']

    def getWaferId(self):
        return self.transceive(Command.create('readChipInformation'))['waferid']

    def getFirmwareVersion(self):
        return self.transceive(Command.create('readFirmwareRelease'))

    def setIntTimesus(self, grayscaleIntTime, lowIntTime,
                      midIntTime=0, highIntTime=0):
        print(f'setIntTimesus({grayscaleIntTime}, {lowIntTime}, {midIntTime}, {highIntTime})')
        self.transceive(Command.create(
            'setIntTimes',
            {'lowIntTime': lowIntTime,
             'midIntTime': midIntTime,
             'highIntTime': highIntTime,
             'grayscaleIntTime': grayscaleIntTime}))

    def setRoi(self, x0, y0, x1, y1):
        print(f'setRoi({x0}, {y0}, {x1}, {y1})')
        self.dut.setColCount(x1-x0)
        self.dut.setRowCount(y1-y0)
        self.transceive(Command.create('setRoi',
                                       {'leftColumn': x0,
                                        'topRow': y0,
                                        'rightColumn': x1,
                                        'bottomRow': y1}))
    def setHdr(self, hdr_mode):
        print(f'setHdr({hdr_mode})')
        self.transceive(Command.create('setHdr', hdr_mode))

    def setBinning(self, binning_type):
        self.transceive(Command.create('setBinning',  np.byte(binning_type)))

    def setDllStep(self, step: int = 0):
        self.transceive(Command.create('setDllStep', step))

    def getGrayscaleAmplitude(self, mode=0, frameCount=1):
        response = np.array([])
        parser = GrayscaleParser()
        for n in range(frameCount):
            try:
                datastream = self.dut.getImageData(
                    Command.create('getGrayscale', mode),
                    self.dut.getFrameByteCount() + parser.headerStruct.size)
                frame = parser.parse(datastream)
                response = np.empty((frameCount, frame.rows, frame.cols), dtype=np.uint16)
                response[n, :, :] = frame.amplitude
            except (ValueError, EOFError, RuntimeError, TimeoutError, struct.error):
                response[:, :, :] = self.getErrorData()
                break
        return response

    def getTofDistance(self, mode=0, frameCount=1):
        response = np.array([])
        parser = DistanceParser()
        for n in range(frameCount):
            try:
                datastream = self.dut.getImageData(
                    Command.create('getDistance', mode),
                    self.dut.getFrameByteCount() + parser.headerStruct.size)
                frame = parser.parse(datastream)
                response = np.empty((frameCount, frame.rows, frame.cols), dtype=np.uint16)
                response[n, :, :] = frame.distance
            except (ValueError, EOFError, RuntimeError, TimeoutError, struct.error):
                response[:, :, :] = self.getErrorData()
                break
        return response

    def getTofAmplitude(self, mode=0, frameCount=1):
        return self.getTofDistanceAndAmplitude(mode=mode, frameCount=frameCount)[1]

    def getTofDistanceAndAmplitude(self, mode=0, frameCount=1):
        distance = np.array([])
        amplitude = np.array([])
        parser = DistanceAndAmplitudeParser()
        for n in range(frameCount):
            try:
                datastream = self.dut.getImageData(
                    Command.create('getDistanceAndAmplitude', mode),
                    2 * self.dut.getFrameByteCount() + parser.headerStruct.size)
                frame = parser.parse(datastream)
                distance = np.empty((frameCount,frame.rows,frame.cols), dtype=np.uint16)
                amplitude = np.empty((frameCount,frame.rows,frame.cols), dtype=np.uint16)
                distance[n, :, :] = frame.distance
                amplitude[n, :, :] = frame.amplitude
            except (ValueError, EOFError, RuntimeError, TimeoutError, struct.error):
                distance[:, :, :] = self.getErrorData()
                amplitude[:, :, :] = self.getErrorData()
                break
        return distance, amplitude

    def getDcs(self, mode=0, frameCount=1):
        response = np.array([])
        parser = DcsParser()

        for n in range(frameCount):
            try:
                datastream = self.dut.getImageData(
                    Command.create('getDcs', mode),
                    4 * self.dut.getFrameByteCount() + parser.headerStruct.size)
                frame = parser.parse(datastream)
                response = np.empty((frameCount, 4, frame.rows, frame.cols), dtype=np.uint16)
                response[n, :, :, :] = frame.dcs
            except (ValueError, EOFError, RuntimeError, TimeoutError, struct.error):
                response[:, :, :, :] = self.getErrorData()
                break
        return response
    
    def getPointCloud(self, mode=0, frameCount=1):
        # capture depth image & corrections
        depth = self.getTofDistance(mode, frameCount)
        depth = np.rot90(depth, 1, (2, 1))[0]
        depth  = depth.astype(np.float32)
        depth[depth >= self.maxDepth] = np.nan

        # calculate point cloud from the depth image
        points = 1E-3 * self.lensProjection.transformImage(np.fliplr(depth))
        points = np.transpose(points, (1, 2, 0))
        points = points.reshape(-1, 3)
        return points

    def getErrorData(self):
        """Return a matrix of '-1's to indicate a failure in data read out. """
        nrows, ncols = self.dut.getRowCount(), self.dut.getColCount()
        return np.array([[-1 for col in range(ncols)]
                         for row in range(nrows)], dtype=np.uint16)

    def getChipTemperature(self):
        return self.transceive(Command.create('getTemperature'))

    def stopStreaming(self):
        self.transceive(Command.create('stopStream'))

    def systemReset(self):
        self.dut.interface.transmit(Command.create('systemReset'))

    def powerReset(self):
        self.dut.interface.transmit(Command.create('powerReset'))

    def jumpToBootloader(self):
        self.dut.interface.transmit(Command.create('jumpToBootloader'))

    def setMinAmplitude(self, minimum):
        print(f'setMinAmplitude({minimum})')
        self.transceive(Command.create('setMinAmplitude', minimum))

    def setFilter(self, enableMedianFilter, enableAverageFilter, edgeDetectionThreshold, 
                  temporalFilterFactor, temporalFilterThreshold, interferenceDetectionLimit, interferenceDetectionUseLastValue):
        print(f'setFilter({enableMedianFilter}, {enableAverageFilter}, {edgeDetectionThreshold}, {temporalFilterFactor}, {temporalFilterThreshold}, {interferenceDetectionLimit}, {interferenceDetectionUseLastValue})')
        self.transceive(Command.create(
            'setFilter',
            {'temporalFilterFactor': temporalFilterFactor,
             'temporalFilterThreshold': temporalFilterThreshold,
             'enableMedianFilter': enableMedianFilter,
             'enableAverageFilter': enableAverageFilter,
             'edgeDetectionThreshold': edgeDetectionThreshold,
             'interferenceDetectionUseLastValue': interferenceDetectionUseLastValue,
             'interferenceDetectionLimit':  interferenceDetectionLimit}))
        
    def disableFilter(self):
        self.transceive(Command.create(
            'setFilter',
            {'temporalFilterFactor': 0,
             'temporalFilterThreshold': 0,
             'enableMedianFilter': 0,
             'enableAverageFilter': 0,
             'edgeDetectionThreshold': 0,
             'interferenceDetectionUseLastValue': 0,
             'interferenceDetectionLimit': 0}))

    def setModulationFrequencyMHz(self, modulationFrequencyMHz, channel=0):
        print(f'setModulationFrequencyMHz({modulationFrequencyMHz}, {channel})')
        # logging.log(logging.INFO, f'setModulationFrequencyMHz({modulationFrequencyMHz}, {channel})')
        self.transceive(Command.create(
            'setModulationFrequency',
            {'frequencyCode': {12: 0,
                               24: 1,
                               6: 2,
                               5: 0,  # for TOFcam660-H1
                               3: 3,
                               1.5: 4,
                               0.75: 5}[modulationFrequencyMHz],
             'channel': channel}))

    def disableBinning(self):
        self.transceive(Command.create('setBinning', 0))

    def disableHdr(self):
        self.transceive(Command.create('setHdr', 0))

    def setDataIpAddress(self, ipAddress='10.10.31.180'):
        self.transceive(Command.create('setDataIpAddress', ipAddress))

    def setCameraIpAddress(self, ipAddress='10.10.31.180',
                           subnetMask='255.255.255.0',
                           gateway='0.0.0.0'):
        self.transceive(Command.create(
            'setCameraIpAddress',
            {'ipAddress': ipAddress,
             'subnetMask': subnetMask,
             'gateway': gateway}))

    def setRandomMacAddress(self):
        macAddress = generateRandomMacAddress()
        self.transceive(Command.create('setCameraMacAddress', macAddress))
        return macAddress

    def turnOnGrayscalIllumination(self):
        self.transceive(Command.create('setGrayscaleIllumination', 1))

    def turnOffGrayscalIllumination(self):
        self.transceive(Command.create('setGrayscaleIllumination', 0))

    def calibrate(self, logfilename):
        try:
            self.dut.calibrate(Command.create('calibrateProduction'), logfilename)
        finally:
            self.systemReset()
            self.shutdown()
            self.startup()

    def setCompensation(self, setDrnuCompensation=True,setTemperatureCompensation=True,setAmbientLightCompensation=True,setGrayscaleCompensation=True):
        return self.transceive(Command.create('setCompensation', {'setDrnuCompensationEnabed': setDrnuCompensation,
                                                                  'setTemperatureCompensationEnabled': setTemperatureCompensation,
                                                                  'setAmbientLightCompensationEnabled': setAmbientLightCompensation,
                                                                  'setGrayscaleCompensationEnabled': setGrayscaleCompensation,
                                                                  }))
    
    def setLensType(self, lensType):
        self.lensProjection = Lense_Projection.from_lense_calibration(lensType)
