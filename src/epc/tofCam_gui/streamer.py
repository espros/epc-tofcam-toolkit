import logging
import threading
from typing import Callable, Optional

import numpy as np
from PySide6.QtCore import QThread, QTimer, Signal

log = logging.getLogger('Streamer')
log.setLevel(logging.DEBUG)


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
            logging.error(
                f"running function {func} failed with exception: {e}")
        if running:
            self.streamer.start_stream()
    return wrapper


class Streamer(QThread):
    signal_new_frame = Signal(np.ndarray)

    def __init__(self, get_frame_cb: Optional[Callable[[], np.ndarray]] = None,
                 start_stream_cb: Optional[Callable[[], None]] = None,
                 stop_stream_cb:  Optional[Callable[[], None]] = None,
                 post_start_cb: Optional[Callable[[], None]] = None,
                 post_stop_cb:  Optional[Callable[[], None]] = None):
        super(Streamer, self).__init__()
        self.get_frame_cb = get_frame_cb
        self.start_stream_cb = start_stream_cb
        self.stop_stream_cb = stop_stream_cb
        self.post_start_cb = post_start_cb
        self.post_stop_cb = post_stop_cb
        self.__is_streaming = False
        self._fps = 0.0
        self._frame_count = 0
        self._frame_count_lock = threading.Lock()
        self._fps_interval_s = 0.6
        self._fps_timer = QTimer()
        self._fps_timer.setInterval(int(self._fps_interval_s * 1000))
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_smoothing_factor = 0.2

    def getFPS(self):
        return self._fps
    
    def set_fps_smoothing_factor(self, factor = 0.2):
        """update fps smoothing factor. (0 = full responsive, 1 = fully smoothed)"""
        with self._frame_count_lock:
            self._fps_smoothing_factor = factor

    def is_streaming(self):
        return self.__is_streaming

    def start_stream(self, **kwargs):
        if self.__is_streaming:
            logging.warning("Already streaming")
            return
        if not self.get_frame_cb:
            logging.error("Cannot start stream: no get_frame_cb set")
            return
        if self.start_stream_cb:
            log.debug('Running start_stream_cb')
            self.start_stream_cb(**kwargs)
        self._fps = 0.0
        self._frame_count = 0
        self._fps_timer.start()
        self.start()
        if self.post_start_cb:
            log.debug('Running post_start_cb')
            self.post_start_cb(**kwargs)

    def stop_stream(self, **kwargs):
        if not self.is_streaming():
            return
        if self.stop_stream_cb:
            log.debug('Running stop_stream_cb')
            try:
                self.stop_stream_cb(**kwargs)
            except Exception as e:
                log.error(f"stop_stream_cb failed with exception: {e}")
        log.info("Stopping stream")
        self.__is_streaming = False
        self.wait()
        self._fps_timer.stop()
        self._fps = 0.0
        if self.post_stop_cb:
            log.debug('Running post_stop_cb')
            self.post_stop_cb(**kwargs)

    def _update_fps(self):
        """Called by the QTimer every _fps_interval_s seconds to compute FPS."""
        with self._frame_count_lock:
            count = self._frame_count
            self._frame_count = 0
        fps = count / self._fps_interval_s
        self._fps = (1-self._fps_smoothing_factor) * fps + self._fps_smoothing_factor * self._fps

    def run(self):
        self.setPriority(QThread.Priority.LowestPriority)
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

            with self._frame_count_lock:
                self._frame_count += 1
            self.signal_new_frame.emit(image)

        log.debug("Streamer stopped")
