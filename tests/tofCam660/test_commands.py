import pytest
from epc.tofCam660 import TOFcam660
import re
from ..config import DUT_CONFIG


@pytest.fixture(scope="module")
def cam():
    # Get the list of configuration values to parametrize over
    (cam_class, interface) = DUT_CONFIG["dut_TOFcam660"]
    cam: TOFcam660 = cam_class(**interface)
    cam.initialize()
    return cam


def NotImplementedError_Helper(fw_version: str, capability: str, exception_message: str):
    # in case the command is not supported by the firmware, we get a NotImplementedError (detected by python framework)
    assert cam._version >= fw_version, f"This firmware version is actually capable of {capability}"
    assert re.search("Current version:", exception_message) is True, "Decorator error expected, but got something different"


@pytest.mark.systemTest
class Test_setting_calls:
    @pytest.mark.parametrize('integration_times', [[12, 34, 56, 78],
                                                   [25, 16, 0, 0]])
    def test_get_integration_time(self, cam: TOFcam660, integration_times: list[int]):
        cam.settings.set_integration_hdr(integration_times)
        read = cam.settings.get_integration_time()
        assert read['grayscaleIntTime'] == integration_times[0], "Grayscale integration time not set correctly"
        assert read['lowIntTime'] == integration_times[1], "Low integration time not set correctly"
        assert read['midIntTime'] == integration_times[2], "Mid integration time not set correctly"
        assert read['highIntTime'] == integration_times[3], "High integration time not set correctly"

    def test_set_illuminator_segments(self, cam: TOFcam660):
        try:
            cam.settings.set_illuminator_segments(segment_1_on=True, segment_2_on=True, segment_3_on=True, segment_4_on=True)
            # No way to test success here, as the camera always reports ACK
        except NotImplementedError as e:
            NotImplementedError_Helper("3.25", "setting illumination segments", str(e.args))


@pytest.mark.systemTest
class Test_device_calls:
    def test_get_calibration_data(self, cam: TOFcam660):
        try:
            calibData = cam.device.get_calibration_data()
            assert calibData is not None, "calibration data unavailable"
        except NotImplementedError as e:
            NotImplementedError_Helper("3.29", "getting calibration data", str(e.args))

    def test_set_and_get_data_transfer_protocol(self, cam: TOFcam660):
        protocols = ["UDP", "TCP", "UDP"]
        for proto in protocols:
            try:
                cam.device.set_data_transfer_protocol(proto)
                assert cam.device.get_data_transfer_protocol() == proto, "Protocol has not been set"
            except NotImplementedError as e:
                NotImplementedError_Helper("3.43", "getting/setting data transfer protocol", str(e.args))            


@pytest.mark.systemTest
class Test_flexMod_calls:
    @pytest.mark.parametrize('capture_func', ['get_distance_image', 'get_amplitude_image'])
    def test_get_image_functions(self, cam: TOFcam660, capture_func):
        # set to FlexMod
        try:
            cam.settings.set_flex_mod_freq(12)
            assert cam.settings.flexMod == True, "FlexMod has not been enabled"
            assert cam._calibData24Mhz is not None, "24MHz modulation frequency calibration unavailable"
        except RuntimeError as e:
            # in case setting to FlexMod is not allowed, we'll get a RuntimeError with error code 8 (camera response).
            assert cam.settings.flexMod == False, "FlexMod has been enabled"
            assert cam._calibData24Mhz is None, "24MHz modulation frequency calibration would have been available"
            assert re.search("failed with response 8", str(e.args)) is True, "Error code 8 expected, but got something different"
        except NotImplementedError as e:
            NotImplementedError_Helper("3.27", "setting FlexMod modulation frequency", str(e.args))

        # get image
        try:
            roi = cam.settings.get_roi()
            image = getattr(cam, capture_func)()
            assert image.shape == (roi[3], roi[2]), "ROI not matching"
        except NotImplementedError as e:
            NotImplementedError_Helper("3.51", "getting FlexMod images", str(e.args))
