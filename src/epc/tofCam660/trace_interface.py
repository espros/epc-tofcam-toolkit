import select
import socket


class TraceInterface:
    def __init__(self, ipAddress='10.10.31.180', port=50661):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.connect((ipAddress, port))

    def close(self):
        self.socket.close()

    def pollTraceData(self, timeout_s):
        """ The trace interface strings are null terminated"""
        if select.select([self.socket], [], [], timeout_s)[0]:
            return self.socket.recv(4096).decode('ascii')
        else:
            raise TimeoutError(f'no trace data within {timeout_s}s')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
