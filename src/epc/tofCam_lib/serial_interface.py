from enum import Enum
import serial
from typing import Optional
import serial.tools.list_ports
from epc.tofCam_lib.crc import Crc

class ResponseType(Enum):
    ACK = 0
    NACK = 1
    DATA = 2
    ERROR = 3

class ComInterface:
    def __init__(self, timeout: float):
        self.timeout = timeout

    def transmit(self, cmd: int, data: bytearray) -> tuple[ResponseType, bytearray]:
        raise NotImplementedError('transmit method not implemented')

    def connect(self):
        raise NotImplementedError('connect method not implemented')

    def disconnect(self):
        raise NotImplementedError('disconnect method not implemented')

class SerialInterface(ComInterface):
    HEADER_LEN = 4
    CRC_LEN = 4
    START_MARKER = bytes(0xF5)
    def __init__(self, crc: Crc, vid: int, baudrate: int, port=None, timeout=0.2):
        super().__init__(timeout)

        self.port = port
        self.baudrate = baudrate
        self.vid = vid
        self.crc = crc
        self.connect()
    
    def find_ports(self):
        result = None
        ports = serial.tools.list_ports.comports()
        if len(ports) == 0:
            raise ConnectionError('No serial port found')
        for port in ports:
            if port.vid == 1155:
                print(f'Device found at port:')
                print(f'port: {port.device}, desc: {port.description}, vendor id: {port.vid}')
                result = port.device
        
        if result == None:
            raise ConnectionError('Device not found')
        return result
    
    def _check_crc(self, data: bytearray, crc: bytearray):
        if not self.crc.verify(data, crc):
            raise ValueError('CRC error')
    
    def _send_cmd(self, cmd: int, data: bytearray):
        message = bytearray(self.START_MARKER) + bytearray([cmd]) + data
        crc = self.crc.calculate(message)
        message += bytearray(crc.to_bytes(4, 'little'))
        self.serial.write(message)

    def _get_response(self) -> tuple[ResponseType, bytearray, bytearray]:
        header = self.serial.read(self.HEADER_LEN)
        if header[0:len(self.START_MARKER)] != self.START_MARKER:
            raise ValueError('Invalid start marker')
        responseType = ResponseType(header[1])
        length = header[2] | header[3] << 8
        data = self.serial.read(length)
        crc = self.serial.read(self.CRC_LEN)
        return responseType, bytearray(data), bytearray(crc)
    
    def transmit(self, cmd: int, data: bytearray) -> tuple[ResponseType, bytearray]:
        self._send_cmd(cmd, data)
        respType, data, crc = self._get_response()
        self._check_crc(data, crc)
        return respType, data

    def connect(self):
        if self.port is None:
            self.port = self.find_ports()
        self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
    
    def disconnect(self):
        self.serial.close()