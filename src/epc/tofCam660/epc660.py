import abc
import time
import socket
from epc.tofCam660.memory import Memory
from epc.tofCam660.trace_interface import TraceInterface
from epc.tofCam660.interface import (Interface, UdpInterface,
                                 NullInterface, NullUdpInterface)
from epc.tofCam660.usb_interface import UsbInterface, findPort

class Epc660(abc.ABC):
    def __init__(self, revision):
        self.memory = Memory.create(revision)
        self.interface = NullInterface()
        self.udpInterface = NullUdpInterface()
        self.rowCount = 240
        self.colCount = 320

    def getRegisterAddress(self, registername):
        return self.memory.getAddress(registername)

    def getRowCount(self):
        return self.rowCount

    def getColCount(self):
        return self.colCount
    
    def setRowCount(self, rows):
        self.rowCount = rows

    def setColCount(self, cols):
        self.colCount = cols

    def getFrameByteCount(self):
        return self.getRowCount() * self.getColCount() * 2

    def transceive(self, command):
        return self.interface.transceive(command)

    # @abc.abstractmethod
    def startup(self):
        pass

    # @abc.abstractmethod
    def waitTillCameraBooted(self):
        pass

    # @abc.abstractmethod
    def shutdown(self):
        pass

    # @abc.abstractmethod
    def getImageData(self, command, bytecount):
        pass

    # @abc.abstractmethod
    def calibrate(self, calibrationCommand, logfilename):
        pass


class Epc660Ethernet(Epc660):
    def __init__(self, ip_address='10.10.31.180', tcp_port=50660, udp_port=45454, memRev=0):
        super().__init__(memRev)
        self.interface = Interface(ip_address, tcp_port)
        self.udpInterface = UdpInterface(ip_address, udp_port)

    def shutdown(self):
        self.interface.close()
        self.udpInterface.close()

    def getImageData(self, command, bytecount):
        while True:
            self.interface.transceive(command)
            udpFrame, nBytes = self.udpInterface.receiveFrame()
            if(nBytes > 0):
                return udpFrame
            else:
                raise RuntimeError('failed to receive image data')
        

    def calibrate(self, calibrationCommand, logfilename):
        """The calibrate production command responds immediately with
        a calibrating response. At the end of calibration, either
        acknowledge or error is sent.
        in case:
        - the camera crashes during calibration -> pollTraceData raises a timeout error
        - the calibration fails -> pollResponse receives error and raises a runtime error
        - the calibration passes -> pollResponse raises no exception and breaks the loop"""
        self.transceive(calibrationCommand)
        with open(logfilename, 'wt', buffering=1) as logfh, \
                TraceInterface() as traceInterface:
            while True:
                logfh.write(traceInterface.pollTraceData(timeout_s=100))
                try:
                    print(self.interface.pollResponse(timeout_s=0.1))
                except TimeoutError as e:
                    pass
                else:
                    break


class Epc660Usb(Epc660):
    def startup(self):
        self.interface = UsbInterface()

    def waitTillCameraBooted(self):
        for i in range(20):
            if findPort():
                break
            time.sleep(1)
        else:
            raise RuntimeError('no camera found')

    def shutdown(self):
        self.interface.close()

    def getImageData(self, command, bytecount):
        return self.interface.transceive(command)

    def calibrate(self, calibrationCommand, logfilename):
        self.transceive(calibrationCommand)
        text = ''
        with open(logfilename, 'wt', buffering=1) as logfh:
            while True:
                try:
                    text = self.interface.pollTraceData(timeout_s=100)
                    logfh.write(text + '\n')
                    if 'Full Calibration finished' in text:
                        break
                except TimeoutError:
                    break
        self.interface.pollResponse(timeout_s=100)
