import logging
import numpy as np  
from typing import Optional
from PySide6.QtCore import QThread, Signal

def pause_streaming(func):
    def wrapper(self, *args, **kwargs):
        running = self.streamer.is_streaming()
        if running:
            self.streamer.stop_stream()
        func(self, *args, **kwargs)
        if running:
            self.streamer.start_stream()
    return wrapper

class Streamer(QThread):
    signal_new_frame = Signal(np.ndarray)
    def __init__(self, get_frame_cb: Optional[callable]=None, 
                       start_stream_cb: Optional[callable]=None, 
                       stop_stream_cb:  Optional[callable]=None):
        super(Streamer, self).__init__()
        self.get_frame_cb = get_frame_cb
        self.start_stream_cb = start_stream_cb
        self.stop_stream_cb = stop_stream_cb
        self.__is_streaming = False

    def set_frame_capture_cb(self, get_frame_cb: callable):
        self.get_frame_cb = get_frame_cb

    def is_streaming(self):
        return self.__is_streaming

    def start_stream(self, **kwargs):
        if self.__is_streaming:
            logging.warning("Already streaming")
            return
        if not self.get_frame_cb:
            logging.error("Starting stream")
            return
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