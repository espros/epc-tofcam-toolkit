import logging
import traceback
import numpy as np  
from typing import Optional, Callable
from PySide6.QtCore import QThread, Signal

log = logging.getLogger('Streamer')

def pause_streaming(func):
    """Decorator to pause the streaming while the decorated function is running.\n
    Decorated function needs to be a class member function and have an attribute called streamer of type Streamer.
    """
    def wrapper(self, *args, **kwargs):
        running = self.streamer.is_streaming()
        if running:
            self.streamer.stop_stream()
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            logging.error(f"running function {func} failed with exception: {e}")
        if running:
            self.streamer.start_stream()
    return wrapper

class Streamer(QThread):
    signal_new_frame = Signal(np.ndarray)
    def __init__(self, get_frame_cb: Optional[Callable[[], np.ndarray]]=None, 
                       start_stream_cb: Optional[Callable[[], None]]=None, 
                       stop_stream_cb:  Optional[Callable[[], None]]=None, 
                       post_start_cb: Optional[Callable[[], None]]=None,
                       post_stop_cb:  Optional[Callable[[], None]]=None):
        super(Streamer, self).__init__()
        self.get_frame_cb = get_frame_cb
        self.start_stream_cb = start_stream_cb
        self.stop_stream_cb = stop_stream_cb
        self.post_start_cb = post_start_cb
        self.post_stop_cb = post_stop_cb
        self.__is_streaming = False

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
            log.debug('Running start_stream_cb')
            self.start_stream_cb(**kwargs)
        self.start()
        if self.post_start_cb:
            log.debug('Running post_start_cb')
            self.post_start_cb(**kwargs)

    def stop_stream(self, **kwargs):
        if not self.__is_streaming:
            return
        if self.stop_stream_cb:
            log.debug('Running stop_stream_cb')
            self.stop_stream_cb(**kwargs)
        self.__is_streaming = False
        self.wait()
        if self.post_stop_cb:
            log.debug('Running post_stop_cb')
            self.post_stop_cb(**kwargs)

    def run(self):
        self.__is_streaming = True
        if not self.get_frame_cb:
            raise ValueError("No get_frame_cb set")
        log.debug("Streamer started")
        while self.__is_streaming:
            try:
                image = self.get_frame_cb()
            except Exception as e:
                log.error(f"Failed to get frame with exception: {e}")
                continue
            self.signal_new_frame.emit(image)
        log.debug("Streamer stopped")