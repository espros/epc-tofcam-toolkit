import select
import socket
import struct
from threading import Lock
from epc.tofCam660.response import Response
from epc.tofCam660.parser import Parser
from epc.tofCam660.communicationType import communicationType

import logging
from typing import Optional
import threading


class NullInterface:
    def close(self):
        pass

class NullUdpInterface:
    def close(self):
        pass

class Interface:
    markerStart = 0xffffaa55
    markerStartBytes = struct.pack('!I', markerStart)
    markerEnd = 0xffff55aa
    markerEndBytes = struct.pack('!I', markerEnd)

    def __init__(self, ipAddress='10.10.31.180', port=50660):
        self.lock = Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.open = False
        try: 
            self.socket.connect((ipAddress, port))
            self.open = True
        except Exception as e:
            raise ConnectionError(f'No camera found at address {ipAddress}:{port}\n{e}')

    def close(self):
        self.socket.close()
        self.open = False

    def is_socket_closed(self) -> bool:
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            previous_blocking_state = self.socket.getblocking()
            self.socket.setblocking(False)
            data = self.socket.recv(16, socket.MSG_PEEK)
            self.socket.setblocking(previous_blocking_state)
            if len(data) == 0:
                return True
        except BlockingIOError:
            self.socket.setblocking(previous_blocking_state)
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            # unexpected exception when checking if a socket is closed
            return True
        
        return False

    def transceive(self, command):
        self.lock.acquire()
        self.transmit(command)
        response = self.receive()
        self.lock.release()
        if response.isError():
            raise RuntimeError(f'command {command} failed with response {response}')
        return response

    def transmit(self, command):
        message = self._assembleMessage(command)
        self.socket.sendall(message)

    def _assembleMessage(self, command):
        payload = command.toBytes()
        return (self.markerStartBytes + struct.pack('!I', len(payload)) +
                payload + self.markerEndBytes)

    def receive(self):
        size = self._receiveHeader()
        payload = self.receiveBytes(size)
        self._receiveFooter()
        return Response.fromBytes(payload)

    def _receiveHeader(self):
        response = self.receiveBytes(struct.calcsize('!II'))
        startmarker, size = struct.unpack('!II', response)
        if not startmarker == self.markerStart:
            raise ValueError('Start marker not correct: 0x{:08x}'.format(startmarker))
        return size

    def _receiveFooter(self):
        response = self.receiveBytes(struct.calcsize('!I'))
        endmarker = struct.unpack('!I', response)[0]
        if not endmarker == self.markerEnd:
            raise ValueError('End marker not correct: 0x{:08x}'.format(endmarker))

    def receiveBytes(self, size):
        message = bytearray()
        while len(message) < size:
            if (size - len(message)) > 4096:
                part = self.socket.recv(4096)
            else:
                part = self.socket.recv(size - len(message))
            if not part:
                raise EOFError('Could not receive all expected data')
            message += part
        return message

    def pollResponse(self, timeout_s):
        if select.select([self.socket], [], [], timeout_s)[0]:
            response = self.receive()
            if response.isError():
                raise RuntimeError(f'error response {response}')
            return response
        else:
            raise TimeoutError(f'no response within {timeout_s}s')
  
class UdpPacket:
    def __init__(self, data) -> None:
        self.packetHeaderFormat = struct.Struct('!HIHIII')
        (self.measurementId,
         self.totalSize,
         self.packetSize,
         self.offset,
         self.packetCount,
         self.packetNumber, ) = self.packetHeaderFormat.unpack(data[:20])
        self.data = data[20:]

class TcpReceiver:
    def __init__(self, ipAddress='10.10.31.180', port: int = 45454, timeout_s: int = 2):
        self.lock = Lock()
        self.ipAddress = ipAddress
        self.port = port
        self.timeout_s = timeout_s
        self.data = bytearray()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ipAddress, self.port))
        self.clearInputBuffer()

    def clearInputBuffer(self):
        """Clear the input buffer of the socket."""
        try:
            current_state = self.socket.getblocking()
            self.socket.setblocking(False)
            while True:
                self.socket.recv(4096)
        except BlockingIOError:
            pass
        except ConnectionResetError:
            raise ConnectionError(f'Connection to camera at {self.ipAddress}:{self.port} was reset.')
        finally:
            self.socket.setblocking(current_state)

    def close(self):
        self.socket.close()

    def receiveFrame(self):
        class HeaderParser(Parser):
            def parseData(self, frame):
                pass

        try:
            # get first packet and unpack header information
            first_chunk = self.socket.recv(8096)
            partialFrame = HeaderParser().parse(first_chunk, True)
            buffer_size = HeaderParser().headerStruct.size + \
                (
                    partialFrame.cols * partialFrame.rows * \
                    communicationType().get_item_by_id(id=partialFrame.measurementType).bytes_per_pixel
                )
            data_buffer = bytearray(buffer_size)
            data_buffer[0:len(first_chunk)] = first_chunk
            byteCount = len(first_chunk)

            # Receive remaining data
            while byteCount < buffer_size:
                chunk = self.socket.recv(buffer_size - byteCount)
                if not chunk:
                    break  # Connection closed by the server
                data_buffer[byteCount:byteCount + len(chunk)] = chunk
                byteCount += len(chunk)

        except ConnectionError as e:
            raise ConnectionError(f'No camera found at address {self.ipAddress}:{self.port}\n{e}')
        except socket.timeout as to:
            raise TimeoutError(f"Could not receive frame, camera timed out({self.timeout_s} s)")
          
        return data_buffer, byteCount

class UdpInterface:
    def __init__(self, ipAddress='10.10.31.180', port=45454):
        self.ipAddress = ipAddress
        self.port = port
        self.packetHeaderFormat = struct.Struct('!HIHIII')
        self.data = bytearray()
        self.index = 0
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udpSocket.bind(('', self.port))
        self.udpSocket.settimeout(1)

    def close(self):
        self.udpSocket.close()

    def receiveFrame(self):
        packets = []
        
        while True:
            try:
                udpPacket, (ipAddress, _) = self.udpSocket.recvfrom(4096)
            except socket.timeout:
                print('udp interface timeout')
                break

            if ipAddress != self.ipAddress:
                continue

            packet = UdpPacket(udpPacket)
            packets.append(packet)
            
            if packet.packetCount-1 == packet.packetNumber:
                break

        frameData = bytearray(packets[0].totalSize)
        byteCount = 0
        for p in packets:
            frameData[p.offset:p.offset+p.packetSize] = p.data
            byteCount += p.packetSize
        return frameData, byteCount

    # def receive(self, bytecount):
    #     self.data = bytearray(bytecount)
    #     self.index = 0
    #     while True:
    #         try:
    #             udpPacket, (ipAddress, port) = self.udpSocket.recvfrom(4096)
    #         except socket.timeout:
    #             print('udp interface timeout')
    #             break
    #         if ipAddress == self.ipAddress:
    #             self.appendPacket(udpPacket)
    #         if self.index >= bytecount:
    #             break
    #     return self.data[:bytecount]

    # def appendPacket(self, udpPacket):
    #     # (measurementId,
    #     #  totalSize,
    #     #  packetSize,
    #     #  totalPacketCount,
    #     #  packetNumber,
    #     #  offset, ) = self.packetHeaderFormat.unpack(
    #     #      udpPacket[:self.packetHeaderFormat.size])
    #     payload = udpPacket[self.packetHeaderFormat.size:]
    #     self.data[self.index:self.index + len(payload)] = payload
    #     self.index += len(payload)

class TraceInterface:
    def __init__(self, ipAddress='10.10.31.180', port=50661, logFile=None):
        # Setup logging
        self.logging = False
        self.logger = logging.getLogger('tofCam660.trace')
        self.logger.setLevel(logging.INFO)
        self.log_formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
        self.log_file_handler = None
        if logFile:
            self.setLogFile(logFile)

        # Setup connection to the trace interface
        self.ipAddress = ipAddress
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # Start logging thread
        self._thread = threading.Thread(target=self._logTraceData)

    def startLogging(self, logFile: Optional[str] = None):
        """Start logging trace data in a separate thread."""
        if self.logging:
            self.logger.warning('Trace logging is already running.')
            return
        
        if logFile:
            self.setLogFile(logFile)

        self.socket.connect((self.ipAddress, self.port))

        self.logging = True
        self._thread = threading.Thread(target=self._logTraceData)
        self._thread.start()

    def stopLogging(self):
        """Stop logging trace data."""
        if self.logging:
            self.logging = False
            self.socket.close()
            self._thread.join()

    def _logTraceData(self):
        """ Continuously poll trace data and log it """
        self.logger.info('Trace logging started.')
        while True:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.logger.warning('Connection closed by the server')
                    self.logging = False
                    break
                trace_data = data.decode('ascii').strip()
                if trace_data:
                    self.logger.info(trace_data)
            except Exception as e:
                self.logger.error(f'Error while polling trace data: {e}')
                self.logging = False
                break

        self.logger.info('Trace logging stopped.')

    def setLogFile(self, logFile):
        """Set the log file for the trace interface."""
        if self.log_file_handler:
            self.logger.removeHandler(self.log_file_handler)
        self.log_file_handler = logging.FileHandler(logFile)
        self.log_file_handler.setLevel(logging.DEBUG)
        self.log_file_handler.setFormatter(self.log_formatter)
        self.logger.addHandler(self.log_file_handler)