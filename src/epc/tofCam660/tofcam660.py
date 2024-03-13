import numpy as np
from epc.tofCam_lib import TOFcam, TOF_Settings_Controller, Dev_Infos_Controller
from epc.tofCam660.epc660 import Epc660Ethernet
from epc.tofCam660.interface import Interface, UdpInterface
from epc.tofCam660.memory import Memory
from epc.tofCam660.command import Command
from epc.tofCam660.parser import GrayscaleParser, DistanceParser, AmplitudeParser, DistanceAndAmplitudeParser, DcsParser

class TOFcam660_Settings(TOF_Settings_Controller):
    def __init__(self, tcp: Interface) -> None:
        super().__init__()
        self.roi = (0, 0, 320, 240)
        self.tcp_interface = tcp
        self.captureMode = 0

    def transceive(self, cmd: Command) -> None:
        self.tcp_interface.transceive(cmd)

    def set_integration_time(self, gray_us: int, low_us: int, mid_us: int, high_us: int) -> None:
        self.transceive(Command.create(
            'setIntTimes',
            {'lowIntTime': low_us,
             'midIntTime': mid_us,
             'highIntTime': high_us,
             'grayscaleIntTime': gray_us}))
        
    def set_roi(self, x1: int, y1: int, x2: int, y2: int):
        self.roi = (x1, y1, x2, y2)
        self.transceive(Command.create('setRoi',
                                       {'leftColumn': x1,
                                        'topRow': y1,
                                        'rightColumn': x2,
                                        'bottomRow': y2}))
        
    def set_hdr(self, mode: str) -> None:
        self.transceive(Command.create('setHdr', mode))

    def set_binning(self, binning_type):
        self.transceive(Command.create('setBinning',  np.byte(binning_type)))

    def set_dll_steps(self, step: int = 0):
        self.transceive(Command.create('setDllStep', step))

    def set_min_amplitude(self, minimum: int):
        self.transceive(Command.create('setMinAmplitude', minimum))

    def set_grayscale_illumination(self, enable=True):
        self.transceive(Command.create('setGrayscaleIllumination', int(enable)))

    def set_compensations(self, setDrnuCompensation=True,
                              setTemperatureCompensation=True,
                              setAmbientLightCompensation=True,
                              setGrayscaleCompensation=True):
        self.transceive(Command.create('setCompensation', { 'setDrnuCompensationEnabed': setDrnuCompensation,
                                                            'setTemperatureCompensationEnabled': setTemperatureCompensation,
                                                            'setAmbientLightCompensationEnabled': setAmbientLightCompensation,
                                                            'setGrayscaleCompensationEnabled': setGrayscaleCompensation}))

    def set_filters(self, enableMedianFilter: bool, 
                          enableAverageFilter: bool, 
                          edgeDetectionThreshold: int, 
                          temporalFilterFactor: int, 
                          temporalFilterThreshold: int, 
                          interferenceDetectionLimit: int, 
                          interferenceDetectionUseLastValue: bool):
        self.transceive(Command.create(
            'setFilter',
            {'temporalFilterFactor': temporalFilterFactor,
             'temporalFilterThreshold': temporalFilterThreshold,
             'enableMedianFilter': enableMedianFilter,
             'enableAverageFilter': enableAverageFilter,
             'edgeDetectionThreshold': edgeDetectionThreshold,
             'interferenceDetectionUseLastValue': interferenceDetectionUseLastValue,
             'interferenceDetectionLimit':  interferenceDetectionLimit}))
        
    def disable_filters(self):
        self.set_filters(False, False, 0, 0, 0, 0, False)

    def set_modulation_frequency(self, frequency_mhz: int, channel=0):
        self.transceive(Command.create(
            'setModulationFrequency',
            {'frequencyCode': {12: 0,
                               24: 1,
                               6: 2,
                               5: 0,  # for TOFcam660-H1
                               3: 3,
                               1.5: 4,
                               0.75: 5}[frequency_mhz],
             'channel': channel}))
        
        

class TOFcam660_Device_Infos(Dev_Infos_Controller):
    def __init__(self, tcp: Interface) -> None:
        super().__init__()
        self.tcp_interface = tcp

    def write_register(self, reg_addr: int, value: int) -> None:
        self.tcp_interface.transceive(Command.create('writeRegister', {'address': reg_addr, 'value': value}))

    def read_register(self, reg_addr: int) -> int:
        return self.tcp_interface.transceive(Command.create('readRegister', {'address': reg_addr}))
    
    def get_chip_infos(self) -> int:
        chipInfos = self.tcp_interface.transceive(Command.create('readChipInformation'))
        return chipInfos['chipid'], chipInfos['waferid']
    
    def get_fw_version(self) -> str:
        return self.tcp_interface.transceive(Command.create('readFirmwareRelease'))

    def get_chip_temperature(self):
        return self.transceive(Command.create('getTemperature'))
    
    def system_reset(self):
        self.tcp_interface.transmit(Command.create('systemReset'))

    def power_reset(self):
        self.tcp_interface.transmit(Command.create('powerReset'))

    def jump_to_bootloader(self):
        self.tcp_interface.transmit(Command.create('jumpToBootloader'))

    def set_udp_ip_address(self, ipAddress='10.10.31.180'):
        self.transceive(Command.create('setDataIpAddress', ipAddress))

    def set_camera_ip_address(self, ipAddress='10.10.31.180',
                           subnetMask='255.255.255.0',
                           gateway='0.0.0.0'):
        self.transceive(Command.create(
            'setCameraIpAddress',
            {'ipAddress': ipAddress,
             'subnetMask': subnetMask,
             'gateway': gateway}))

    

class TOFcam660(TOFcam):
    def __init__(self, ip_address='10.10.31.180', tcp_port=50660, udp_port=45454):
        super().__init__(TOFcam660_Settings(), TOFcam660_Device_Infos())
        self.tcpInterface = Interface(ip_address, tcp_port)
        self.udpInterface = UdpInterface(ip_address, udp_port)
        self.memory = Memory.create(0)

    def __del__(self):
        self.tcpInterface.close()
        self.udpInterface.close()

    def initialize(self):
        pass

    def get_grayscale_image(self):
        response = np.array([])
        parser = GrayscaleParser()
        try:
            datastream = self.dut.getImageData(
                Command.create('getGrayscale', self.settings.captureMode),
                self.dut.getFrameByteCount() + parser.headerStruct.size)
            frame = parser.parse(datastream)
            image = frame.amplitude
        except Exception as e:
            raise Exception(f"Failed to get grayscale image: {e}")
        return response
    
    def get_distance_image(self):
        parser = DistanceParser()
        try:
            datastream = self.dut.getImageData(
                Command.create('getDistance', self.settings.captureMode),
                self.dut.getFrameByteCount() + parser.headerStruct.size)
            frame = parser.parse(datastream)
        except Exception as e:
            raise Exception(f"Failed to get distance image: {e}")
        return frame.distance
    
    def get_distance_and_amplitude(self):
        parser = DistanceAndAmplitudeParser()
        try:
            datastream = self.dut.getImageData(
                Command.create('getDistanceAndAmplitude', self.settings.captureMode),
                2 * self.dut.getFrameByteCount() + parser.headerStruct.size)
            frame = parser.parse(datastream)
        except Exception as e:
            raise Exception(f"Failed to get distance and amplitude image: {e}")
            
        return frame.distance, frame.amplitude

    def get_amplitude_image(self):
        return self.get_distance_and_amplitude()[1]
    
    def get_dcs_images(self, mode=0, frameCount=1):
        parser = DcsParser()

        try:
            datastream = self.dut.getImageData(
                Command.create('getDcs', mode),
                4 * self.dut.getFrameByteCount() + parser.headerStruct.size)
            frame = parser.parse(datastream)
        except Exception as e:
            raise Exception(f"Failed to get DCS image: {e}")
        
        return frame.dcs