from typing import Any

from epc.tofCam_lib.h5Cam import (H5_Settings_Controller, H5Cam,
                                  H5Dev_Infos_Controller, ReadOnlyError)


class H5cam635_Settings(H5_Settings_Controller):
    """Read the cam settings from an H5 database"""
    pass


class H5cam635_Device(H5Dev_Infos_Controller):
    """This class is used to control the device information of the TOFcam635 camera.
    """

    def get_device_ids(self) -> tuple[int, int, int, int]:
        """Device ids

        Returns:
            tuple[int, int, int, int]: hwVersion, deviceType, chipType, oPmode
        """
        return tuple(self._get_attribute("device_ids"))

    def system_reset(self) -> None:
        raise ReadOnlyError(f"H5Cam635 is readonly! It can only read the previously set values, cannot do system_reset!")

    def get_calibration_info(self) -> Any:
        return tuple(self._get_attribute("calibration_info"))


class H5cam635(H5Cam):

    def get_distance_and_amplitude_image(self):
        """returns a tuple of 2d arrays (distance, amplitude)"""
        pass
