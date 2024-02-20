

class TOF_Settings_Controller:
    def __init__(self) -> None:
        pass
    
    def set_integration_time(self, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'set_integration_time' jet")

    def set_modulation_frequency(self, frequency_mhz: int):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'set_modulation_frequency' jet")

    def set_roi(self, x: int, y: int, width: int, height: int):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'set_roi' jet")

    def set_minimal_amplitude(self, amplitude: int):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'set_minimal_amplitude' jet")

class Dev_Infos_Controller:
    def __init__(self) -> None:
        pass

    def get_chip_temperature(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_chip_temperature' jet")

    def get_chip_id(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_chip_id' jet")

    def get_wafer_id(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_wafer_id' jet")

    def get_fw_version(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_fw_version' jet")

    def get_hw_version(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_hw_version' jet")

    def get_device_id(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_device_id' jet")

class TOFcam:
    def __init__(self, settings_ctrl: TOF_Settings_Controller, info_ctrl: Dev_Infos_Controller) -> None:
        self.settings = settings_ctrl
        self.device = info_ctrl

    def get_distance_image(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_distance_image' jet")

    def get_amplitude_image(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_amplitude_image' jet")

    def get_grayscale_image(self):
        raise NotImplementedError(f"{self.__class__.__name__} has not implemented 'get_grayscale_image' jet")