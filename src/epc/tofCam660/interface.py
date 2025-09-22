import select
import socket
import struct
from threading import Lock, Thread
from epc.tofCam660.response import Response
import logging
from typing import Optional
from epc.tofCam660.parser import Parser

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
        self.ip_address = ipAddress
        self.port = port
        self.lock = Lock()
        self.connect()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try: 
            self.socket.connect((self.ip_address, self.port))
        except Exception as e:
            raise ConnectionError(f'No camera found at address {self.ip_address}:{self.port}\n{e}')
        self.socket.settimeout(1)

    def close(self):
        self.socket.close()

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
        self.lock.acquire(timeout=0.5)
        try:
            self.transmit(command)
            response = self.receive()
        except TimeoutError:
            raise TimeoutError(f"Not able to transmit the command \"{command.__class__.__name__}\" successfully")
        finally:
            self.lock.release()
        if response.isError():
            raise RuntimeError(f'Command \"{command.__class__.__name__}\" failed with response {response}')
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
    def __init__(self, ipAddress='10.10.31.180', port: int = 45454, timeout_s: int = 1):
        self.lock = Lock()
        self.ip_address = ipAddress
        self.port = port
        self.timeout_s = timeout_s
        self.data = bytearray()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip_address, self.port))
        self.turnOffDelayedAck()
        self.clearInputBuffer()
        self.socket.settimeout(self.timeout_s)

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
            raise ConnectionError(f'Connection to camera at {self.ip_address}:{self.port} was reset.')
        finally:
            self.socket.setblocking(current_state)

    def close(self):
        self.socket.close()

    def turnOffDelayedAck(self):
        # The TCP_QUICKACK setting is transient, so we set it multiple times,
        # especially in the receiving loop to ensure it remains active.
        # TCP_QUICKACK is an option that forces an ACK (acknowledgment) packet
        # to be sent for every individual packet received, rather than delaying
        # ACKs for multiple packets. Although this may seem counterintuitive,
        # it can actually improve performance. The reason is that the
        # system-dependent delay in waiting for new packets to arrive can be
        # longer than the time it takes to send an ACK immediately.
        # By using TCP_QUICKACK, we have observed better overall results.
        #
        # The availability of TCP_QUICKACK depends on the platform and python version.
        # Adapt measures on system level if system does not support it.
        try:
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        except (AttributeError, OSError):
            pass

    def receiveFrame(self):
        class HeaderParser(Parser):
            def parseData(self, frame):
                pass

        try:
            # get first packet and unpack header information
            self.turnOffDelayedAck()
            first_chunk = self.socket.recv(8096)
            partialFrame = HeaderParser().parse(first_chunk)
            buffer_size = HeaderParser().headerStruct.size + \
                (
                    partialFrame.cols * partialFrame.rows * \
                    CommunicationType().get_item_by_id(id=partialFrame.measurementType).bytes_per_pixel
                )
            data_buffer = bytearray(buffer_size)
            data_buffer[0:len(first_chunk)] = first_chunk
            byteCount = len(first_chunk)

            # Receive remaining data
            while byteCount < buffer_size:
                self.turnOffDelayedAck()
                chunk = self.socket.recv(buffer_size - byteCount)
                if not chunk:
                    break  # Connection closed by the server
                data_buffer[byteCount:byteCount + len(chunk)] = chunk
                byteCount += len(chunk)

        except ConnectionError as e:
            raise ConnectionError(f'No camera found at address {self.ip_address}:{self.port}\n{e}')
        except socket.timeout:
            raise TimeoutError(f"TCP data interface timed out")
          
        return data_buffer, byteCount

class UdpInterface:
    def __init__(self, ipAddress='10.10.31.180', port=45454):
        self.ip_address = ipAddress
        self.port = port
        self.packetHeaderFormat = struct.Struct('!HIHIII')
        self.data = bytearray()
        self.index = 0
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


        # Important if camera supports large data and streaming modes:
        #
        # Read back the buffer size
        recv_buf_size = self.udpSocket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        #print(f"Receive buffer size: {recv_buf_size} bytes")
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        if recv_buf_size < 1024 * 1024:
            #Set receive buffer size to 1MB
            try:
                self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                #print("[Unix] Set receive buffer size to 1MB")
            except (AttributeError, OSError):
                # SO_RCVBUF setting may not be available on all platforms
                pass
        recv_buf_size = self.udpSocket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        #print(f"Receive buffer size adjusted: {recv_buf_size} bytes")

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
                raise TimeoutError(f"UDP data interface timed out")

            if ipAddress != self.ip_address:
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

class CommunicationType():
    class Item:
        def __init__(self, id, bytes_per_pixel, name):
            self.id = id
            self.bytes_per_pixel = bytes_per_pixel
            self.name = name

    items_by_id = {}
    items_by_name = {}

    def __init__(self):
        for item in [ self.Item(0x00, 4, "DATA_DISTANCE_AMPLITUDE"),
            self.Item(0x01, 2, "DATA_DISTANCE"),
            self.Item(0x02, 2, "DATA_AMPLITUDE"),
            self.Item(0x03, 2, "DATA_GRAYSCALE"),
            self.Item(0x04, 8, "DATA_DCS"),
        ]:
            self.items_by_id[item.id] = item
            self.items_by_name[item.name] = item

    def get_item_by_id(self, id: int):
        return self.items_by_id.get(id)

    def get_item_by_name(self, name: str):
        return self.items_by_name.get(name)

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
        self._thread = Thread(target=self._logTraceData)

    def startLogging(self, logFile: Optional[str] = None):
        """Start logging trace data in a separate thread."""
        if self.logging:
            self.logger.warning('Trace logging is already running.')
            return
        
        if logFile:
            self.setLogFile(logFile)

        self.socket.connect((self.ipAddress, self.port))

        self.logging = True
        self._thread = Thread(target=self._logTraceData)
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
