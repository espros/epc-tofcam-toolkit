import pytest
from epc.tofCam660 import TOFcam660
from epc.tofCam635 import TOFcam635
from epc.tofCam611 import TOFcam611
from epc.tofCam_lib import TOFcam
from ..config import DUT_FIXTURES, cam660, cam635, cam611, camrange


@pytest.fixture(scope="function")
def cam(request):
    return request.getfixturevalue(request.param)


@pytest.mark.systemTest
@pytest.mark.parametrize("cam", DUT_FIXTURES, indirect=True)
class Test_general_calls:
    def test_has_attributes(self, cam: TOFcam):
        assert hasattr(cam, 'settings')
        assert hasattr(cam, 'device')

    def test_initialize(self, cam: TOFcam):
        # just test if the method is callable
        cam.initialize()

    @pytest.mark.parametrize('get_image_func', ['get_grayscale_image', 'get_distance_image', 'get_amplitude_image'])
    def test_get_image_functions(self, cam: TOFcam, get_image_func):
        # tests all get image functions and checks if the image has the correct shape
        roi = cam.settings.get_roi()
        image = getattr(cam, get_image_func)()
        assert image.shape == (roi[3], roi[2])


@pytest.mark.systemTest
@pytest.mark.parametrize("cam", DUT_FIXTURES, indirect=True)
class Test_setting_calls:
    def test_set_roi(self, cam: TOFcam):
        if isinstance(cam, TOFcam611):
            pytest.skip('TOFcam611 does not support setting the ROI.')
        
        old_roi = cam.settings.get_roi()

        if isinstance(cam, TOFcam635):
            rois = [
                (0, 0, 160, 60), # l=160px, h=60px
                (4, 4, 156, 12)  # l=152px, h=8px
            ]
        if isinstance(cam, TOFcam660):
            rois = [
                (0, 0, 320, 240),  # l=320px, h=240px
                (4, 116, 316, 124) # l=312px, h=8px
            ]

        for roi in rois:
            resolution = (roi[3] - roi[1], roi[2] - roi[0])
            readback = cam.settings.set_roi(roi)
            assert readback == roi
            assert cam.settings.get_roi() == roi        
            assert cam.get_amplitude_image().shape == (resolution)
            assert cam.get_distance_image().shape == (resolution)
            assert cam.get_grayscale_image().shape == (resolution)

        # restore old values
        cam.settings.set_roi(old_roi)

    def test_set_modulation(self, cam: TOFcam):
        mod_freqs = cam.settings.get_modulation_frequencies()
        mod_chs = cam.settings.get_modulation_channels()

        for freq in mod_freqs:
            for ch in mod_chs:
                cam.settings.set_modulation(freq, ch)
                cam.get_distance_image() # test that distance image still gets calculated

    @pytest.mark.parametrize('setting_func', ['set_minimal_amplitude', 'set_integration_time', 'set_integration_time_grayscale'])
    def test_set_standard_settings(self, cam: TOFcam, setting_func):
        # test that functions are callable and image can still be received
        if setting_func == 'set_integration_time_grayscale' and isinstance(cam, TOFcam611):
            pytest.skip('TOFcam611 does not support grayscale images.')
        if isinstance(cam, TOFcam660):
            cam.settings.set_hdr(0)
        getattr(cam.settings, setting_func)(100)
        cam.get_distance_image()
        cam.get_grayscale_image()
        cam.get_amplitude_image()
        if isinstance(cam, TOFcam660):
            cam.settings.set_hdr(2)


@pytest.mark.systemTest
@pytest.mark.parametrize("cam", DUT_FIXTURES, indirect=True)
class Test_device_calls:
    def test_get_chip_informations(self, cam: TOFcam):
        chip_id, wafer_id = cam.device.get_chip_infos()
        assert isinstance(chip_id, int)
        assert isinstance(wafer_id, int)

    def test_get_fw_version(self, cam: TOFcam):
        fw_version = cam.device.get_fw_version()
        assert isinstance(fw_version, str)

    def test_get_chip_temperature(self, cam: TOFcam):
        temp = cam.device.get_chip_temperature()
        assert isinstance(temp, float)

    def test_get_device_id(self, cam: TOFcam):
        if isinstance(cam, TOFcam660):
            pytest.skip('Not implemented for TOFcam660')
        device_id = cam.device.get_device_id()
        assert isinstance(device_id, str)

