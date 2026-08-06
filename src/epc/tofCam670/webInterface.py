import threading
import typing

import numpy as np
import requests

from epc.tofCam670.tofCam670 import (
    FrameType,
    TOFControl,
)


class WebInterface:
    """
    Interface for TOFcam670 implementations over HTTP.
    """

    def __init__(self, host="127.0.0.1", port=8000) -> None:
        self.host = host
        self.port = port
        self.session = requests.Session()  # Persistent session for connection pooling

        self._is_streaming = False
        self._lock = threading.Lock()  # used to prevent concurrent next() calls on self.streams
        self._streams: dict[FrameType, typing.Generator[np.ndarray[typing.Tuple[int, int], float], None, None]] = {}

    def set_control(self, control: TOFControl, value: int) -> None:
        url = f"http://{self.host}:{self.port}/settings/{control.name.lower()}?value={int(value)}"
        response = self.session.put(url)
        if response.status_code != 200:
            raise ConnectionError(f"Error {response.status_code}: {response.json()['detail']}")

    def get_device_info(self) -> dict:
        url = f"http://{self.host}:{self.port}/device.json"
        response = self.session.get(url)
        if response.status_code != 200:
            raise ConnectionError(f"Error {response.status_code}: {response.json()['detail']}")
        return response.json()

    def single_capture(self, frame_type: FrameType) -> np.ndarray[typing.Tuple[int, int], float]:
        url = f"http://{self.host}:{self.port}/capture/raw/{frame_type.name.lower()}"
        response = self.session.get(url)
        if response.status_code != 200:
            raise ConnectionError(f"Error {response.status_code}: {url}")
        height = int(response.headers.get("X-Frame-Height"))
        width = int(response.headers.get("X-Frame-Width"))
        buf = response.content  # Binary data as bytes
        arr = np.frombuffer(buf, dtype=np.uint16).reshape(height, width).astype(float)
        return arr

    def _setup_stream(self, frame_type: FrameType) -> typing.Generator[np.ndarray[typing.Tuple[int, int], float], None, None]:
        url = f"http://{self.host}:{self.port}/stream/raw/{frame_type.name.lower()}"
        response = self.session.get(url, stream=True)
        if response.status_code != 200:
            raise ConnectionError(f"Error {response.status_code}: {url}")
        height = int(response.headers.get("X-Frame-Height"))
        width = int(response.headers.get("X-Frame-Width"))
        frame_size = 2 * height * width  # 2 bytes per uint16

        for chunk in response.iter_content(chunk_size=frame_size):
            if len(chunk) == frame_size:
                arr = np.frombuffer(chunk, dtype=np.uint16).reshape(height, width).astype(float)
                yield arr

    def get_frame(self, frame_type: FrameType) -> np.ndarray[typing.Tuple[int, int], float]:
        frame = None
        if self._is_streaming:
            if frame_type not in self._streams:
                self._streams[frame_type] = self._setup_stream(frame_type)
            with self._lock:  # concurrent calls on a generator produce an error
                frame = next(self._streams[frame_type])
        else:
            frame = self.single_capture(frame_type)

        if frame_type == FrameType.DCS:
            frame = np.array(np.vsplit(frame, 4))

        return frame

    def get_distance_and_amplitude(self) -> tuple[np.ndarray, np.ndarray]:
        return self.get_frame(FrameType.DISTANCE), self.get_frame(FrameType.AMPLITUDE)

    def start_stream(self):
        self._is_streaming = True
        # we do not setup any streams here, they will be lazily
        # initialzed only when the first frame is requested

    def stop_stream(self):
        self._is_streaming = False
        self._streams.clear()
