import functools

def requires_fw_version(min_version: str = None, max_version: str = None):
    def decorator(func):
        """
        A decorator to restrict method/function execution based on camera firmware version range.

        Args:
            min_version (str, optional): The minimum firmware version required (e.g., "3.39").
                                        If current version is less than this, NotImplementedError is raised.
            max_version (str, optional): The maximum firmware version allowed (e.g., "3.42").
                                        If current version is greater than this, NotImplementedError is raised.
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
