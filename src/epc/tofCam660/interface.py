import select
import socket
import struct
from threading import Lock
from epc.tofCam660.response import Response


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
        try: 
            self.socket.connect((ipAddress, port))
        except Exception as e:
            raise ConnectionError(f'No camera found at address {ipAddress}:{port}\n{e}')

    def close(self):
        self.socket.close()

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
