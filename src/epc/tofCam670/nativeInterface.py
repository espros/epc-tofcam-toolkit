import logging
import subprocess

import epc_tofcam_native as native
import numpy as np
from epc_tofcam_native import TOFCam as libcam

from epc.tofCam670.tofCam670 import (
    FrameType,
    TOFControl,
)

libLogger = logging.getLogger('epc_tofcam_native')
libLogger.setLevel(logging.INFO)


class NativeInterface:

    def __init__(self):
        self.cam = libcam()
        self.cam.open()

    def set_control(self, control: TOFControl, value: int) -> None:
        self.cam.setControl(native.TOFControl(control.value), value)

    def _get_chip_infos(self):
        try:
            result = subprocess.run(
                ["v4l2-ctl", "-d", "/dev/v4l-subdev2", "-C", "device_id"],
                capture_output=True, text=True, timeout=5
            )
            device_id = result.stdout.strip()
            # Format: "device_id: 'epc670-0x00-0x04-0x0F-0x00-00008-00105'"
            parts = device_id.split('-')
            wafer_id = int(parts[-2])
            chip_id = int(parts[-1].rstrip("'"))
            return chip_id, wafer_id
        except Exception as e:
            return 0, 0

    def _get_fw_version(self):
        try:
            with open("/sys/module/cam_epc670/version", "r") as f:
                return f.read().strip()
        except OSError:
            return "0.0.0"

    def get_device_info(self) -> dict:
        # Implement device info retrieval if needed
        return {
            "chip_id": self._get_chip_infos()[0],
            "wafer_id": self._get_chip_infos()[1],
            "fw_version": self._get_fw_version(),
        }

    def single_capture(self, frame_type: FrameType) -> np.ndarray:
        return self.get_frame(native.FrameType(frame_type.value))

    def get_frame(self, frame_type: FrameType) -> np.ndarray:
        frame = self.cam.captureFrame()
        if FrameType.DCS == frame_type:
            return np.array([frame.get(native.FrameType.DCS, i) for i in range(4)])
        return frame.get(native.FrameType(frame_type.value))

    def get_distance_and_amplitude(self) -> tuple[np.ndarray, np.ndarray]:
        frame = self.cam.captureFrame()
        return frame.get(native.FrameType.DISTANCE), frame.get(native.FrameType.AMPLITUDE)

    def start_stream(self):
        self.cam.startStream()

    def stop_stream(self):
        self.cam.stopStream()
