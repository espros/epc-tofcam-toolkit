import os
import queue
import h5py
import numpy as np
from datetime import datetime
from typing import Tuple, Union
from PySide6.QtCore import QThread, Slot


class HDF5Logger(QThread):

    def __init__(self, image_type, parent=None):
        super().__init__(parent)
        self._meta_data: dict[str, object] = {}
        self._queue: queue.Queue[Union[Tuple[np.ndarray,
                                             float], None]] = queue.Queue()
        self._running = False
        if image_type == 'DCS':
            self._preprocess = self.recreate_dcs_from_image_grid
        else:
            self._preprocess = lambda img: img

    def set_metadata(self, **attrs: object) -> None:
        self._meta_data.update(attrs)

    @Slot(np.ndarray, float)
    def add_frame(self, frame, timestamp):
        if self._running:
            try:
                self._queue.put_nowait((frame, timestamp))
            except queue.Full:
                raise queue.Full(
                    f"Recording Queue is full.")

    @Slot()
    def stop_logging(self):
        self._running = False
        self._queue.put(None)

    def run(self):
        self._running = True

        # prepare filename & open the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logdir = "captured_data"
        os.makedirs(logdir, exist_ok=True)
        filepath = os.path.join(logdir, f"data_{timestamp}.h5")

        with h5py.File(filepath, 'a') as f:

            # write any metadata upfront
            for k, v in self._meta_data.items():
                f.attrs[k] = v

            dset = ts = None
            while True:
                item = self._queue.get()
                if item is None:
                    break

                raw_frame, tstamp = item
                frame = self._preprocess(raw_frame)

                # if this is the first real frame, create the datasets:
                if dset is None or ts is None:

                    shape = frame.shape
                    dset = f.create_dataset(
                        'frames',
                        shape=(0, *shape),
                        maxshape=(None, *shape),
                        dtype=frame.dtype,
                    )
                    ts = f.create_dataset(
                        'timestamps',
                        shape=(0,),
                        maxshape=(None,),
                        dtype='float64'
                    )

                # append frame & timestamp
                idx = dset.shape[0]
                dset.resize(idx+1, axis=0)
                dset[idx, ...] = frame
                ts.resize(idx+1, axis=0)
                ts[idx] = tstamp

    def recreate_dcs_from_image_grid(self, image):
        """
        reconstruct the 4DCS from the 2x2 image grid view.
        returns reconstructed DCS with shape (4, width, height)
        """
        width = image.shape[0]//2
        height = image.shape[1]//2
        dcs = np.zeros((4, height, width), dtype=image.dtype)

        image = image.T
        dcs[0] = image[0:height, 0:width]
        dcs[1] = image[0:height, width:2*width]
        dcs[2] = image[height:2*height, 0:width]
        dcs[3] = image[height:2*height, width:2*width]
        return dcs.transpose((0, 2, 1))
