import queue
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import h5py  # type: ignore
import numpy as np
from PySide6.QtCore import QThread


class HDF5Logger(QThread):
    """HDF5 log worker object, storing streamed images"""

    def __init__(self, image_type: str, file_path: str | Path, parent=None) -> None:
        """

        Args:
            image_type (str): The type of the image "DCS", "Point cloud", .."
            file_path (str | Path): The path the source file
        """
        super().__init__(parent)
        self.image_type = image_type
        self._filepath = file_path
        self._meta_data: Dict[str, Any] = {}
        self._queue: queue.Queue[Optional[Tuple[np.ndarray, float]]] = queue.Queue(
        )
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def set_metadata(self, **attrs: object) -> None:
        self._meta_data.update(attrs)

    def add_frame(self, frame: np.ndarray) -> None:
        """Add a frame with the timestamp flag to the queue"""
        if self._running:
            try:
                self._queue.put_nowait((frame, time.time()))
            except queue.Full:
                raise queue.Full(
                    f"Recording Queue is full.")

    def stop_logging(self) -> None:
        """Stop the data logging by inserting a None to the queue"""
        self._running = False
        self._queue.put(None)

    def run(self) -> None:
        """Main thread loop creating/appending to the datases"""
        self._running = True
        ds_frames = ds_timestamps = None
        with h5py.File(self._filepath, 'a') as f:
            self._store_meta(f)
            while True:
                item = self._queue.get()
                if item is None:
                    break

                _frame, _timestamp = item

                if ds_frames is None and ds_timestamps is None:
                    ds_frames, ds_timestamps = self._init_db(
                        f, shape=_frame.shape, dtype=_frame.dtype)

                self._append(dataset=ds_frames, new=_frame)
                self._append(dataset=ds_timestamps, new=_timestamp)

    def _init_db(self, f: h5py.File, shape: Tuple[int], dtype: str) -> Tuple[h5py.Dataset, h5py.Dataset]:
        """Initialize the frame and timesteps datasets

        Args:
            f (h5py.File): Wirte/Append mode h5 file object
            shape (Tuple[int]): The shape of a single frame
            dtype (str): The type of the dataset

        Returns:
            Tuple[h5py.Dataset, h5py.Dataset]: ds_frames, ds_timestamps
                ds_frames: The frame storage
                ds_timestamps: The timeline storage
        """
        _group = f.require_group(self.image_type)
        ds_frames = _group.create_dataset("frames", shape=(0, *shape),
                                          maxshape=(None, *shape), chunks=(1, *shape), dtype=dtype)
        ds_timestamps = _group.create_dataset("timestamps", shape=(0,),
                                              maxshape=(None,), chunks=(1,), dtype='float64')
        return ds_frames, ds_timestamps

    def _append(self, dataset: h5py.Dataset, new: float | np.ndarray) -> None:
        """Append a new instance to a dataset

        Args:
            dataset (h5py.Dataset): The dataset to append to
            new (float | np.ndarray): New instance
        """
        idx = dataset.shape[0]
        dataset.resize(idx+1, axis=0)
        if isinstance(new, float):
            dataset[idx] = new
        else:
            dataset[idx, ...] = new

    def _store_meta(self, f: h5py.File) -> None:
        """Store the meta information in the top level

        Args:
            f (h5py.File): The append mode file object
        """
        assert f.mode == "r+"
        for k, v in self._meta_data.items():
            f.attrs[k] = v
