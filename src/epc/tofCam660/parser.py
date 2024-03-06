import abc
import struct
import numpy as np


class Frame:
    def __init__(self):
        self.headerVersion = None
        self.measurementType = None
        self.cols = None
        self.rows = None
        self.leftColumn = None
        self.topRow = None
        self.rightColumn = None
        self.bottomRow = None
        self.lowIntTime = None
        self.midIntTime = None
        self.highIntTime = None
        self.temperature = None
        self.dataOffset = None
        self.amplitude = None
        self.distance = None
        self.dcs = None


class Parser(abc.ABC):
    headerStruct = struct.Struct('!BHHHHHHHHHHhH')

    def __init__(self):
        self.bytestream = None

    def parse(self, bytestream):
        self.bytestream = bytestream
        frame = Frame()
        self.parseHeader(frame)
        self.parseData(frame)
        return frame

    def parseHeader(self, frame):
        [frame.headerVersion,
         frame.measurementType,
         frame.cols,
         frame.rows,
         frame.leftColumn,
         frame.topRow,
         frame.rightColumn,
         frame.bottomRow,
         frame.lowIntTime,
         frame.midIntTime,
         frame.highIntTime,
         frame.temperature,
         frame.dataOffset] = self.headerStruct.unpack(self.bytestream[:self.headerStruct.size])
        self.bytestream = self.bytestream[self.headerStruct.size:]
        frame.temperature /= 100

    @abc.abstractmethod
    def parseData(self, frame):
        pass


class GrayscaleParser(Parser):
    def parseData(self, frame):
        frame.amplitude = np.frombuffer(self.bytestream, dtype=np.uint16).reshape(frame.rows, frame.cols)


class DistanceParser(Parser):
    def parseData(self, frame):
        frame.distance = np.frombuffer(self.bytestream, dtype=np.uint16).reshape(frame.rows, frame.cols)


class DistanceAndAmplitudeParser(Parser):
    def parseData(self, frame):
        data = np.frombuffer(self.bytestream, dtype=np.uint16)
        frame.distance = data[::2].reshape(frame.rows, frame.cols)
        frame.amplitude = data[1::2].reshape(frame.rows, frame.cols)


class DcsParser(Parser):
    def parseData(self, frame):
        data = np.frombuffer(self.bytestream, dtype=np.uint16)
        data = data.reshape(4, frame.rows, frame.cols)
        frame.dcs = np.array([data])
