import functools


def requires_device_type(device_type: int):
    """
    A decorator to restrict method/function execution based on camera device type.

    Args:
        device_type (int): The device type that supports executing this method.

    Raises:
        Error: If the current device type does not match the required device type,
                             or if the device type cannot be determined.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, "_device_type"):
                current_device_type = self._device_type
            elif hasattr(self, "cam") and hasattr(self.cam, "_device_type"):
                current_device_type = self.cam._device_type
            else:
                raise NotImplementedError(
                    f"Method '{func.__name__}' requires device type {device_type}, "
                    f"but the device type is unknown."
                )

            if current_device_type != device_type:
                raise NotImplementedError(
                    f"Method '{func.__name__}' is not supported for device type "
                    f"{current_device_type}. Required device type: {device_type}."
                )

            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def requires_fw_version(min_version: str = None, max_version: str = None):
    def decorator(func):
        """
        A decorator to restrict method/function execution based on camera firmware version range.

        Args:
            min_version (str, optional): The minimum firmware version required (e.g., "3.39").
                                         If current version is less than this, NotImplementedError is raised.
            max_version (str, optional): The maximum firmware version allowed (e.g., "3.42").
                                         If current version is greater than this, NotImplementedError is raised.
                                         
        Note: Decorating two methods with the same name will cause the second method to overwrite the first.
              It's how Python handles method definitions. When you define a method, you are essentially
              assigning a function object to a name within a class. If you define the same name twice, the
              second definition replaces the first one entirely.
              That said, it is not possible using this decorator to write two methods, one for firmwares
              before and one for firmwares after a certain version. For such cases, version checking needs
              to be done within the method itself.

        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            current_version = ""
            if hasattr(self, "_version"):
                current_version = self._version
            elif hasattr(self, "cam") and hasattr(self.cam, "_version"):
                current_version = self.cam._version
            else:
                raise NotImplementedError(
                    f"Method '{func.__name__}' requires a specific camera version. Current version camera version is unknown."
                )
                       
            if min_version and current_version < min_version:
                raise NotImplementedError(
                    f"Method '{func.__name__}' requires camera version {min_version} or higher. Current version: {current_version}."
                )
            
            if max_version and current_version > max_version:
                raise NotImplementedError(
                    f"Method '{func.__name__}' is not compatible with camera versions newer than {max_version}. Current version: {current_version}"
                )
            # If all checks pass, execute the original function
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
