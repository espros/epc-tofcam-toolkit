import os
import select
import serial
import serial.tools.list_ports
import struct
from epc.tofCam660.response import Response
from epc.tofCam660.crc import Crc
from sys import platform


def findPort():
    # change this value for USB connection to the port the cam is connected to
    # you can find the correct port in the device manager
    manually_set_port = 'COM6'

    # automatic usb exploration deactivated (work in progress, not releavant for ToFcam660)
    # LINUX
    #    if(platform=='linux'):
    #        for dirpath, dirnames, filenames in os.walk('/dev/serial/by-id/'):
    #            for filename in filenames:
    #                if 'NXP_SEMICONDUCTORS_MCU_VIRTUAL_COM_DEMO' in filename:
    #                    return os.path.join(dirpath, filename)
    # WIN
    #   else:
    #      automatic='dummystring'
    #     ports=list(serial.tools.list_ports.comports())
    #    for p in ports:
    #       if(p.vid==8137):
    #                automatic=p.device
    #                return automatic
    #
    return manually_set_port


class UsbInterface:
    transmitMarkerStart = struct.pack('B', 0xf5)

    def __init__(self):
        port = findPort()
        self.sif = serial.Serial(port, timeout=0.5)
        self.crc = Crc()

    def close(self):
        self.sif.close()

    def transceive(self, command, responsePacketCount=1):
        self.transmit(command)
        return self.receive(responsePacketCount)

    def transmit(self, command):
        self.sif.write(self._assembleMessage(command))

    def receive(self, responsePacketCount):
        data = bytearray()
        for i in range(responsePacketCount):
            header, responseType, size = self._receiveHeader()
            payload = self.receiveBytes(size + 4)
            crc = struct.unpack('<I', payload[-4:])[0]
            part = payload[:-4]
            if not self.crc.isCrcCorrect(header + part, crc):
                raise ValueError(f'crc not correct, received: 0x{crc:08x}')
            data += part
        return self.createResponse(responseType, data)

    def createResponse(self, responseType, data):
        if self.responseTypeIsAnswer(responseType):
            response = Response.fromBytes(data)
            if response.isError():
                raise RuntimeError(str(response))
        elif self.responseTypeIsImageData(responseType):
            response = data
        else:
            raise ValueError(f'unknown response type: {responseType}')
        return response

    def responseTypeIsAnswer(self, responseType):
        return responseType == 0

    def responseTypeIsImageData(self, responseType):
        return responseType == 1

    def _assembleMessage(self, command):
        payload = command.toBytes()
        message = self.transmitMarkerStart + payload
        crc = self.crc.calcCrc32(message)
        return message + bytes(struct.pack('<I', crc))

    def _receiveHeader(self):
        """ After connecting a camera to a running usb interface,
        the first 16 bytes are nonsense. Try a few times for the
        real response to arrive.
        """
        for i in range(10):
            response = self.receiveBytes(6)
            startmarker, responseType, size = struct.unpack('<BBI', response)
            if startmarker == 0xfa:
                break
        else:
            raise ValueError('start marker not correct: 0x{:02x}'.format(startmarker))
        return response, responseType, size

    def receiveBytes(self, size):
        data = self.sif.read(size)
        if not len(data) == size:
            raise TimeoutError(f'serial interface time out: {len(data)} of {size} received')
        return data

    def pollTraceData(self, timeout_s):
        """ The trace interface strings are null terminated"""
        if select.select([self.sif], [], [], timeout_s)[0]:
            return self.sif.read_until(expected=bytes([0, ]),
                                       size=self.sif.in_waiting).decode('ascii')
        else:
            raise TimeoutError(f'no trace data within {timeout_s}s')

    def pollResponse(self, timeout_s):
        if select.select([self.sif], [], [], timeout_s)[0]:
            response = self.receive(1)
            if response.isError():
                raise RuntimeError(f'error response {response}')
            return response
        else:
            raise TimeoutError(f'no response within {timeout_s}s')
