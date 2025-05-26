import logging
import os
import time
from abc import ABC
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import h5py  # type: ignore
import numpy as np
from PySide6.QtCore import QObject, Signal

from epc.tofCam_lib.tofCam import (Dev_Infos_Controller,
                                   TOF_Settings_Controller, TOFcam)

logger = logging.getLogger("H5Cam")


class ReadOnlyError(ValueError):
    pass


class _H5Base:
    def __init__(self, source: Path | str, group: Optional[str] = None, continuous: bool = False) -> None:
        """

        Args:
            source (Path | str): The `*.h5` file path
            group (Optional[str], optional): The group name that stores the attributes and frames. Defaults to None.
        """

        self.__continuous = continuous
        self._extension = ".h5"
        self.source = source  # type: ignore
        self._attributes: Optional[Dict[str, Any]] = None
        self._recordings: Dict[int, Tuple[float, np.ndarray]] = {}
        self.group = group

        # State params
        self.index = 0
        self._tic = time.time()
        self._prev_timestamp: Optional[float] = None
        self.__timestamps: Optional[np.ndarray] = None

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, val: int) -> None:
        self.__index = val

    def enable_continous(self, val: bool) -> None:
        """Enable/Disable continuous streaming"""
        self.__continuous = val

    @property
    def image_type(self) -> str:
        __attr = self._get_attribute("image_type")
        assert isinstance(__attr, str)
        return __attr

    def __len__(self) -> int:
        """Get the record length in number of frames"""
        if len(self._recordings) == 0:
            self.__getitem__(0)
        return len(self._recordings)

    def __getitem__(self, index: int) -> Tuple[float, np.ndarray]:
        """Read the timestamp and frame from the source"""

        if len(self._recordings) == 0:
            with h5py.File(self.source, "r") as f:
                if self.group is not None:
                    group = f[self.group]
                else:
                    group = f
                _timestamps, _frames = group["timestamps"][:], group["frames"][:]
                _timestamps: np.ndarray
                _frames: np.ndarray
                _recordings = {_i: (float(_ts), _frame) for _i, (_ts, _frame) in enumerate(
                    zip(_timestamps, _frames))}

            self._recordings = _recordings
            self.__timestamps = _timestamps

        if index > len(self._recordings):
            raise StopIteration(
                f"Record length exceeded! {index} > {len(self._recordings)}")

        return self._recordings[index]

    @property
    def source(self) -> Path:
        """The path containing source data"""
        return self.__source  # type: ignore

    @source.setter  # type: ignore
    def source(self, value: str | Path) -> None:
        """Checks and sets the source path

        Args:
            value (Path): The candidate source path to be checked
        """
        if value is None:
            raise ValueError("Source needs to be set for an H5 interaction!")

        if isinstance(value, str):
            value = Path(value)
        if not isinstance(value, Path):
            raise ValueError("Source should be the path the source file")

        if (value.suffix.lower() != self._extension):
            raise ValueError(
                f"The file is not a {self._extension} file {value.suffix.lower()}"
            )
        if not value.exists():
            raise ValueError(f"Filepath {value} does not exist!")
        elif not os.access(value, os.R_OK):
            raise ValueError(
                f"Filepath {value} is not accessible due to access limitations"
            )
        elif not value.is_file():
            raise ValueError(f"The path {value} exists, but it's not a file!")

        self.__source = value

    def _get_attribute(self, key: str) -> Any:
        """Read the attribute from the source"""

        if self._attributes is None:
            with h5py.File(self.source, "r") as f:
                if self.group is not None:
                    group = f[self.group]
                else:
                    group = f
                _attributes = {_key: group.attrs[_key] for _key in group.attrs}
            self._attributes = _attributes

        if key in self._attributes:
            return self._attributes[key]
        else:
            raise IndexError(f"Cannot find attribute {key}")

    def _stream(self) -> Tuple[float, np.ndarray]:
        """Get a stream of frames from the h5 source, in the same speed if continuous mode is enabled

        Args:
            key (str): The image type key

        Returns:
            Tuple[float,np.ndarray]: timestep, frame
                timestep: the timestep when the image has fetched
                frame: the frame instance that that specific timestep
        """

        self._simulate_shutter_delay()
        _timestamp, _frame = self.__getitem__(self.index)
        if self.__continuous:
            self._increment_index()
        return _timestamp, _frame

    def _simulate_shutter_delay(self) -> None:
        """Sleep for at most t_wait time if the time passed is not enough"""
        _toc = time.time()
        _sleep_time = max(self.t_wait - (_toc-self._tic), 0)
        logger.debug(f"Sleeping for {_sleep_time:3.2f} seconds..")
        time.sleep(_sleep_time)
        self._tic = time.time()

    def _increment_index(self) -> None:
        """Inrement the index by 1 and update the previous timestep"""
        if self.index < len(self) - 1:
            self._prev_timestamp = self.timestamp
            self.index += 1
        else:
            self.index = 0
            self._prev_timestamp = self.timestamps[0] - self.dt_mean

    def update_index(self, idx: int) -> None:
        """Update the index and reset the shutter delay"""
        if idx < len(self) and idx >= 0:
            self.index = idx
            self._prev_timestamp = None
        else:
            raise ValueError(
                f"Index update is beyond the limits! 0 <= idx < {len(self)}! idx = {idx}")

    def reset_stream(self) -> None:
        """Set the index to idle position to reset the stream"""
        self.index = 0
        self._prev_timestamp = None

    @property
    def timestamps(self) -> np.ndarray:
        """The timeline of the record"""
        if self.__timestamps is None:
            self.__getitem__(0)
        if self.__timestamps is not None:
            return self.__timestamps
        else:
            raise ValueError("Timestamps cannot be fetched!")

    @property
    def timestamp(self) -> float:
        """The exact timestamp of the current index"""
        return float(self.timestamps[self.index])

    @property
    def duration(self) -> float:
        """The duration of the record, in seconds"""
        return float(self.timestamps[-1] - self.timestamps[0])

    @property
    def time_passed(self) -> float:
        """The exact time passed since the record started, in seconds"""
        return float(self.timestamps[self.index] - self.timestamps[0])

    @property
    def dt_mean(self) -> float:
        """Average time interval between two consecutive frames"""
        if not hasattr(self, "__dt"):
            self.__dt = float(np.mean(np.abs(np.diff(self.timestamps))))
        return self.__dt

    @property
    def fps_mean(self) -> float:
        """Mean fps value"""
        return 1.0/self.dt_mean

    @property
    def t_wait(self) -> float:
        """Time to wait before returning the next frame"""
        if self._prev_timestamp is None:
            return 0
        else:
            return self.timestamp - self._prev_timestamp


class H5_Settings_Controller(ABC, _H5Base, TOF_Settings_Controller):
    def __init__(self, source: str | Path) -> None:
        _H5Base.__init__(self, source=source, group=None, continuous=False)
        TOF_Settings_Controller.__init__(self)

    def get_modulation_frequencies(self) -> list[float]:
        return list(self._get_attribute("modulation_frequencies"))

    def get_modulation(self) -> float:
        """Modulation frequency"""
        return float(self._get_attribute("mod_frequency"))

    def get_modulation_channels(self) -> list[int]:
        return list(self._get_attribute("modulation_channels"))

    def get_roi(self) -> tuple[int, int, int, int]:
        """The region of interest (ROI) of the camera.

        Returns:
            tuple[int, int, int, int]: x0, y0, x1, y1
        """
        return tuple(self._get_attribute("roi"))

    def set_modulation(self, frequency_mhz: float, channel: int = 0):
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set modulation!")

    def set_roi(self, roi: tuple[int, int, int, int]):
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set ROI!")

    def set_minimal_amplitude(self, amplitude: int):
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set minimal aplitude!")

    def set_integration_time(self, int_time_us: int):
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set integration time!")

    def set_integration_time_grayscale(self, int_time_us: int):
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set ingegration time grayscale!")

    def set_dll_step(self, step: int, fine_step=0):
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set DLL step!")

    def set_hdr(self, mode: int) -> None:
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set HDR!")


class H5Dev_Infos_Controller(ABC, _H5Base, Dev_Infos_Controller):
    def __init__(self, source: str | Path) -> None:
        _H5Base.__init__(self, source=source, group=None, continuous=False)
        Dev_Infos_Controller.__init__(self)

    def get_chip_infos(self) -> tuple[int, int]:
        return tuple(self._get_attribute("chip_infos"))

    def get_fw_version(self) -> str:
        return str(self._get_attribute("fw_version"))

    def get_device_id(self) -> Any:
        return self._get_attribute("device_id")

    def read_register(self, reg_addr: int) -> int:
        _val = self._get_attribute(str(reg_addr))
        assert isinstance(_val, int)
        return _val

    def get_chip_temperature(self) -> float:
        logger.critical(
            f"H5Cam is static! It can only read the time depended dynamic values like temperature")
        return -1

    def write_register(self, reg_addr: int, value: int) -> None:
        logger.info(
            f"H5Cam is readonly! It can only read the previously set values, cannot set register!")


class H5Cam(_H5Base, TOFcam, QObject):
    indexChanged = Signal(int)

    def __init__(self, source: str | Path, continuous: bool = True, settings_ctrl: Optional[H5_Settings_Controller] = None, info_ctrl: Optional[H5Dev_Infos_Controller] = None) -> None:

        QObject.__init__(self, parent=None)

        if settings_ctrl is None:
            settings_ctrl = H5_Settings_Controller(source=source)

        if info_ctrl is None:
            info_ctrl = H5Dev_Infos_Controller(source=source)

        _H5Base.__init__(self, source=source, group=None, continuous=continuous)

        if self.source != settings_ctrl.source:
            raise ValueError(
                f"`H5Cam` and `H5_Settings_Controller` source mismatch! {source} != {settings_ctrl.source}")
        if self.source != info_ctrl.source:
            raise ValueError(
                f"`H5Cam` and `H5Dev_Infos_Controller` source mismatch! {source} != {info_ctrl.source}")

        TOFcam.__init__(self, settings_ctrl=settings_ctrl, info_ctrl=info_ctrl)

        # Update tyhpehints
        self.settings: H5_Settings_Controller
        self.device: H5Dev_Infos_Controller

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, val: int) -> None:
        """Emit when the index has been updated"""
        self.__index = val
        self.indexChanged.emit(val)

    def __del__(self) -> None:
        pass

    def initialize(self) -> None:
        pass

    def get_distance_image(self):
        if self.image_type != 'Distance':
            raise ValueError(
                f"This H5Cam recorded {self.image_type}! Not Distance!")
        _timestamp, _frame = self._stream()
        return _frame

    def get_amplitude_image(self):
        if self.image_type != 'Amplitude':
            raise ValueError(
                f"This H5Cam recorded {self.image_type}! Not Amplitude!")
        _timestamp, _frame = self._stream()
        return _frame

    def get_grayscale_image(self):
        if self.image_type != 'Grayscale':
            raise ValueError(
                f"This H5Cam recorded {self.image_type}! Not Grayscale!")
        _timestamp, _frame = self._stream()
        return _frame

    def get_raw_dcs_images(self):
        if self.image_type != 'DCS':
            raise ValueError(
                f"This H5Cam recorded {self.image_type}! Not DCS!")
        _timestamp, _frame = self._stream()
        return _frame

    def get_point_cloud(self):
        if self.image_type != 'Point Cloud':
            raise ValueError(
                f"This H5Cam recorded {self.image_type}! Not Point Cloud!")
        _timestamp, _frame = self._stream()
        return _frame

    @property
    def mod_frequency(self) -> float:
        """Modulation frequency"""
        return float(self._get_attribute("mod_frequency"))


if __name__ == "__main__":
    cam = H5Cam(
        source="/home/uca/repos/hawkeye-application/fw_hawkeye_zephyr/data_20250523_141531.h5")
    for i in range(100):
        _tic = time.time()
        cam._stream()
        print(f"Prev: {cam.index}")
        _toc = time.time()
        print(f"{_toc-_tic}")
