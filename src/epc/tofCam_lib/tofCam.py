import atexit


class TOF_Settings_Controller:
    def __init__(self) -> None:
        pass

    def set_modulation(self, frequency_mhz: float, channel: int = 0):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_modulation_frequency' jet")

    def get_modulation_frequencies(self) -> list[float]:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_modulation_frequencies' jet")

    def get_modulation_channels(self) -> list[int]:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_modulation_channels' jet")

    def get_roi(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_roi' jet")

    def set_roi(self, roi: tuple[int, int, int, int]):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_roi' jet")

    def set_minimal_amplitude(self, amplitude: int):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_minimal_amplitude' jet")

    def set_integration_time(self, int_time_us: int):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_integration_time' jet")

    def set_integration_time_grayscale(self, int_time_us: int):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_integration_time_grayscale' jet")

    def set_dll_step(self, step: int, fine_step = 0):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_dll_step' jet")

    def set_hdr(self, mode: int) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'set_hdr' jet")

class Dev_Infos_Controller:
    def __init__(self) -> None:
        pass

    def get_chip_temperature(self) -> float:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_chip_temperature' jet")

    def get_chip_infos(self) -> tuple[int, int]:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_chip_id' jet")

    def get_fw_version(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_fw_version' jet")

    def get_device_id(self) -> any:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_device_id' jet")

    def write_register(self, reg_addr: int, value: int) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'write_register' jet")

    def read_register(self, reg_addr: int) -> int:
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'read_register' jet")


class TOFcam:
    def __init__(self, settings_ctrl: TOF_Settings_Controller, info_ctrl: Dev_Infos_Controller) -> None:
        self.settings = settings_ctrl
        self.device = info_ctrl
        if hasattr(self, '__del__'):
            atexit.register(self.__del__)
        elif hasattr(self, 'close'):
            atexit.register(self.close)

    def initialize(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'initialize' jet")

    def get_distance_image(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_distance_image' jet")

    def get_amplitude_image(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_amplitude_image' jet")

    def get_grayscale_image(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_grayscale_image' jet")

    def get_raw_dcs_images(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_raw_dcs_image' jet")

    def get_point_cloud(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} has not implemented 'get_point_cloud' jet")
