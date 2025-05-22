import logging
import os
import time
from abc import ABC
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import h5py  # type: ignore
import numpy as np

from epc.tofCam_lib.tofCam import (Dev_Infos_Controller,
                                   TOF_Settings_Controller, TOFcam)

logger = logging.getLogger("H5Cam")


class ReadOnlyError(ValueError):
    pass


class _H5Base:
    def __init__(self, source: Path | str, group: Optional[str] = None) -> None:
        """

        Args:
            source (Path | str): The `*.h5` file path
            group (Optional[str], optional): The group name that stores the attributes and frames. Defaults to None.
        """

        self._extension = ".h5"
        self.source = source  # type: ignore
        self._attributes: Optional[Dict[str, Any]] = None
        self._recordings: Dict[str, Dict[int, Tuple[float, np.ndarray]]] = {}
        self.group = group

        # State params
        self.index: Dict[str, int] = {}
        self._prev_timestep = None

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

    def _get_frame(self, key: str, index: int) -> Tuple[float, np.ndarray]:
        """Read the timestamp and frame from the source"""

        if key not in self._recordings:
            with h5py.File(self.source, "r") as f:
                if self.group is not None:
                    group = f[self.group]
                else:
                    group = f
                if key in group:
                    group = group[key]
                else:
                    raise IndexError(f"{key} not in recorded!")
                _timestamps, _frames = group["timestamps"][:], group["frames"][:]
                _timestamps: np.ndarray
                _frames: np.ndarray
                _recordings = {key: {_i: (float(_ts), _frame) for _i, (_ts, _frame) in enumerate(zip(_timestamps, _frames))}}

            self._recordings = _recordings

        if index > len(self._recordings[key]):
            raise StopIteration(f"Record length exceeded! {index} > {len(self._recordings[key])}")

        return self._recordings[key][index]

    def _stream_next(self, key: str) -> Tuple[float, np.ndarray]:
        """Get a stream of frames from the h5 source, in the same speed

        Args:
            key (str): The image type key

        Returns:
            Tuple[float,np.ndarray]: timestep, frame
                timestep: the timestep when the image has fetched
                frame: the frame instance that that specific timestep
        """
        if key not in self.index:
            self.index[key] = 0

        _timestamp, _frame = self._get_frame(key, self.index[key] % self._get_record_length(key))
        self.index[key] += 1

        if self._prev_timestep is not None:

            time.sleep(_timestamp - self._prev_timestep)
            self._prev_timestep = _timestamp

        return _timestamp, _frame

    def _get_record_length(self, key: str) -> int:
        """Get the record length of a specific recording"""
        if key not in self._recordings:
            self._get_frame(key, 0)
        return len(self._recordings[key])


class H5_Settings_Controller(ABC, _H5Base, TOF_Settings_Controller):
    def __init__(self, source: str | Path) -> None:
        _H5Base.__init__(self, source=source, group=None)
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
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set modulation!")

    def set_roi(self, roi: tuple[int, int, int, int]):
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set ROI!")

    def set_minimal_amplitude(self, amplitude: int):
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set minimal aplitude!")

    def set_integration_time(self, int_time_us: int):
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set integration time!")

    def set_integration_time_grayscale(self, int_time_us: int):
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set ingegration time grayscale!")

    def set_dll_step(self, step: int, fine_step=0):
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set DLL step!")

    def set_hdr(self, mode: int) -> None:
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set HDR!")


class H5Dev_Infos_Controller(ABC, _H5Base, Dev_Infos_Controller):
    def __init__(self, source: str | Path) -> None:
        _H5Base.__init__(self, source=source, group=None)
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
        logger.critical(f"H5Cam is static! It can only read the time depended dynamic values like temperature")
        return -1

    def write_register(self, reg_addr: int, value: int) -> None:
        logger.info(f"H5Cam is readonly! It can only read the previously set values, cannot set register!")


class H5Cam(ABC, _H5Base, TOFcam):
    def __init__(self, source: str | Path, settings_ctrl: Optional[H5_Settings_Controller] = None, info_ctrl: Optional[H5Dev_Infos_Controller] = None) -> None:

        if settings_ctrl is None:
            settings_ctrl = H5_Settings_Controller(source=source)

        if info_ctrl is None:
            info_ctrl = H5Dev_Infos_Controller(source=source)

        _H5Base.__init__(self, source=source, group=None)

        if self.source != settings_ctrl.source:
            raise ValueError(f"`H5Cam` and `H5_Settings_Controller` source mismatch! {source} != {settings_ctrl.source}")
        if self.source != info_ctrl.source:
            raise ValueError(f"`H5Cam` and `H5Dev_Infos_Controller` source mismatch! {source} != {info_ctrl.source}")

        TOFcam.__init__(self, settings_ctrl=settings_ctrl, info_ctrl=info_ctrl)

        # Update tyhpehints
        self.settings: H5_Settings_Controller
        self.device: H5Dev_Infos_Controller

    def __del__(self) -> None:
        pass

    def initialize(self) -> None:
        pass

    def get_distance_image(self):
        pass

    def get_amplitude_image(self):
        pass

    def get_grayscale_image(self):
        pass

    def get_raw_dcs_images(self):
        __key = "DCS"
        _timestamp, _frame = self._stream_next(__key)
        return _frame

    def get_point_cloud(self):
        pass

    @property
    def mod_frequency(self) -> float:
        """Modulation frequency"""
        return float(self._get_attribute("mod_frequency"))
