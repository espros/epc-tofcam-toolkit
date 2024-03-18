import pytest
from epc.tofCam660 import TOFcam660
from epc.tofCam635 import TOFcam635
from epc.tofCam611 import TOFcam611
from epc.tofCam_lib.tofCam import TOFcam

@pytest.fixture(scope='class')
def tofCam(request):
    tofcam = request.param()
    tofcam.initialize()
    return tofcam

@pytest.mark.systemTest
@pytest.mark.parametrize('tofCam', [TOFcam660, TOFcam635, TOFcam611], indirect=True)
class Test_general_calls:
    def test_has_attributes(self, tofCam: TOFcam):
        assert hasattr(tofCam, 'settings')
        assert hasattr(tofCam, 'device')

    def test_initialize(self, tofCam: TOFcam):
        # just test if the method is callable
        tofCam.initialize()

    @pytest.mark.parametrize('get_image_func', ['get_grayscale_image', 'get_distance_image', 'get_amplitude_image'])
    def test_get_image_functions(self, tofCam: TOFcam, get_image_func):
        # tests all get image functions and checks if the image has the correct shape
        roi = tofCam.settings.get_roi()
        image = getattr(tofCam, get_image_func)()
        assert image.shape == (roi[2], roi[3])


@pytest.mark.systemTest
@pytest.mark.parametrize('tofCam', [TOFcam660, TOFcam635, TOFcam611], indirect=True)
class Test_setting_calls:
    def test_set_roi(self, tofCam: TOFcam):
        if isinstance(tofCam, TOFcam611):
            pytest.skip('TOFcam611 does not support setting the ROI.')
        old_roi = tofCam.settings.get_roi()
        test_roi = 0, old_roi[3]//4, old_roi[2]//2, 3*old_roi[3]//4 # tofcam660 needs symetric y values
        test_roi = tofCam.settings.set_roi(test_roi)
        assert tofCam.settings.get_roi() == test_roi
        
        resolution = (test_roi[2] - test_roi[0], test_roi[3] - test_roi[1])
        assert tofCam.get_amplitude_image().shape == (resolution)
        assert tofCam.get_distance_image().shape == (resolution)
        assert tofCam.get_grayscale_image().shape == (resolution)

        tofCam.settings.set_roi(old_roi)

    def test_set_modulation(self, tofCam: TOFcam):
        mod_freqs = tofCam.settings.get_modulation_frequencies()
        mod_chs = tofCam.settings.get_modulation_channels()

        for freq in mod_freqs:
            for ch in mod_chs:
                tofCam.settings.set_modulation(freq, ch)
                tofCam.get_distance_image() # test that distance image still gets calculated

    @pytest.mark.parametrize('setting_func', ['set_minimal_amplitude', 'set_integration_time', 'set_integration_time_grayscale'])
    def test_set_standard_settings(self, tofCam: TOFcam, setting_func):
        # test that functions are callable and image can still be received
        if setting_func == 'set_integration_time_grayscale' and isinstance(tofCam, TOFcam611):
            pytest.skip('TOFcam611 does not support grayscale images.')
        if isinstance(tofCam, TOFcam660):
            tofCam.settings.set_hdr(0)
        getattr(tofCam.settings, setting_func)(100)
        tofCam.get_distance_image()
        tofCam.get_grayscale_image()
        tofCam.get_amplitude_image()
        if isinstance(tofCam, TOFcam660):
            tofCam.settings.set_hdr(2)


@pytest.mark.systemTest
@pytest.mark.parametrize('tofCam', [TOFcam660, TOFcam635, TOFcam611], indirect=True)
class Test_device_calls:
    def test_get_chip_informations(self, tofCam: TOFcam):
        chip_id, wafer_id = tofCam.device.get_chip_infos()
        assert isinstance(chip_id, int)
        assert isinstance(wafer_id, int)

    def test_get_fw_version(self, tofCam: TOFcam):
        fw_version = tofCam.device.get_fw_version()
        assert isinstance(fw_version, str)

    def test_get_chip_temperature(self, tofCam: TOFcam):
        temp = tofCam.device.get_chip_temperature()
        assert isinstance(temp, float)

    def test_get_device_id(self, tofCam: TOFcam):
        if isinstance(tofCam, TOFcam660):
            pytest.skip('Not implemented for TOFcam660')
        device_id = tofCam.device.get_device_id()
        assert isinstance(device_id, str)

