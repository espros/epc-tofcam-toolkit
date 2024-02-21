import time
import threading
import numpy as np  
from typing import Optional
from PySide6.QtCore import QThread, Signal

class Streamer(QThread):
    signal_new_frame = Signal(np.ndarray)
    def __init__(self, get_frame_cb: callable, 
                       start_stream_cb: Optional[callable]=None, 
                       stop_stream_cb:  Optional[callable]=None):
        super(Streamer, self).__init__()
        self.get_frame_cb = get_frame_cb
        self.start_stream_cb = start_stream_cb
        self.stop_stream_cb = stop_stream_cb
        self.__is_streaming = False

        if not self.get_frame_cb:
            raise ValueError("get_frame_cb must be a callable")


    def is_streaming(self):
        return self.__is_streaming

    def start_stream(self, **kwargs):
        if self.__is_streaming:
            raise Exception("Already streaming")
        if self.start_stream_cb:
            self.start_stream_cb(**kwargs)
        self.start()

    def stop_stream(self, **kwargs):
        if not self.__is_streaming:
            return
        if self.stop_stream_cb:
            self.stop_stream_cb(**kwargs)
        self.__is_streaming = False
        self.wait()

    def run(self):
        self.__is_streaming = True
        while self.__is_streaming:
            image = self.get_frame_cb()
            self.signal_new_frame.emit(image)