import os
import queue
import h5py
import numpy as np
from datetime import datetime
from typing import Tuple, Union
from PySide6.QtCore import QThread, Slot


class HDF5Logger(QThread):

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self._meta_data: dict[str, object] = {}
        self._queue: queue.Queue[Union[Tuple[np.ndarray,
                                             float], None]] = queue.Queue()
        self._running = False
        self.width = width
        self.height = height

    def set_metadata(self, **attrs: object) -> None:
        self._meta_data.update(attrs)

    @Slot(np.ndarray, float)
    def add_frame(self, frame, timestamp):
        # slot to receive a new frame
        if self._running:
            try:
                self._queue.put_nowait((frame, timestamp))
            except queue.Full:
                pass

    @Slot()
    def stop_logging(self):
        self._running = False
        # push a sentinel so run() will unblock and exit
        self._queue.put(None)

    def run(self):
        # opens HDF5 file and store queued frames
        self._running = True

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_{timestamp}.h5"
        logdir = "captured_data"
        os.makedirs(logdir, exist_ok=True)
        filepath = os.path.join(logdir, filename)

        with h5py.File(filepath, 'a') as f:

            # store global metadata
            for k, v in self._meta_data.items():
                f.attrs[k] = v

            if 'frames' not in f:
                dset = f.create_dataset(
                    'frames',
                    shape=(0, self.width*2, self.height*2),
                    maxshape=(None, self.width*2, self.height*2),
                    dtype='uint16'
                )
                ts = f.create_dataset(
                    'timestamps',
                    shape=(0,),
                    maxshape=(None,),
                    dtype='float64'
                )
            else:
                dset = f['frames']
                ts = f['timestamps']

            # store data
            while True:
                item = self._queue.get()
                if item is None:
                    break

                frame, timestamp = item
                idx = dset.shape[0]
                dset.resize(idx+1, axis=0)
                ts.resize(idx+1, axis=0)
                dset[idx, ...] = frame
                ts[idx] = timestamp
