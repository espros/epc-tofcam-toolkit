import struct


class Command:
    """Use factory method 'create(commandName, ...)' to instantiate"""
    commandId = None

    @staticmethod
    def create(commandName, data=None):
        try:
            return commands[commandName](data)
        except KeyError:
            raise ValueError('there is no command {}'.format(commandName))

    def __init__(self, data):
        self.data = data

    def toBytes(self):
        payload = struct.pack('!H', self.commandId) + self.dataToBytes()
        payload += bytes(34 - len(payload))
        return payload

    def dataToBytes(self):
        """overwrite me to implement different byte arrangement of data"""
        if self.data is None:
            return bytes()
        else:
            return bytes((self.data,))

    def __repr__(self):
        if self.data is not None:
            try:
                dataString = ', '.join(['0x{:02x}'.format(entry) for entry in self.data])
            except TypeError:
                dataString = hex(self.data)
            except ValueError:
                dataString = str(self.data)
        else:
            dataString = ''
        return 'command: {}, data: [{}]'.format(self.__class__.__name__, dataString)


class SetRoi(Command):
    commandId = 0

    def dataToBytes(self):
        return struct.pack('!HHHH',
                           self.data['leftColumn'],
                           self.data['topRow'],
                           self.data['rightColumn'],
                           self.data['bottomRow'])


class SetIntTimes(Command):
    commandId = 1

    def dataToBytes(self):
        return struct.pack('!HHHH',
                           self.data['lowIntTime'],
                           self.data['midIntTime'],
                           self.data['highIntTime'],
                           self.data['grayscaleIntTime'])


class GetDistanceAndAmplitude(Command):
    commandId = 2


class GetDistance(Command):
    commandId = 3


class GetGrayscale(Command):
    commandId = 5


class GetDcs(Command):
    commandId = 7


class StopStream(Command):
    commandId = 6


class SystemReset(Command):
    commandId = 45


class PowerReset(Command):
    commandId = 69


class JumpToBootloader(Command):
    commandId = 111


class SetMinAmplitude(Command):
    commandId = 21

    def dataToBytes(self):
        return struct.pack('!H', self.data)


class SetFilter(Command):
    commandId = 22

    def dataToBytes(self):
        return struct.pack('!HHBBHBH',
                           self.data['temporalFilterFactor'],
                           self.data['temporalFilterThreshold'],
                           self.data['enableMedianFilter'],
                           self.data['enableAverageFilter'],
                           self.data['edgeDetectionThreshold'],
                           self.data['interferenceDetectionUseLastValue'],
                           self.data['interferenceDetectionLimit'])


class SetModulationFrequency(Command):
    commandId = 23

    def dataToBytes(self):
        return struct.pack('!BBB',
                           self.data['frequencyCode'],
                           self.data['channel'],
                           0)


class SetBinning(Command):
    commandId = 24


class SetHdr(Command):
    commandId = 25


class ReadChipInformation(Command):
    commandId = 36


class ReadFirmwareRelease(Command):
    commandId = 37


class SetDllStep(Command):
    commandId = 29


class WriteRegister(Command):
    commandId = 42

    def dataToBytes(self):
        return struct.pack('!BB',
                           self.data['address'],
                           self.data['value'])


class ReadRegister(Command):
    commandId = 43

    def dataToBytes(self):
        return struct.pack('!B', self.data['address'])


class GetTemperature(Command):
    commandId = 74


class SetDataIpAddress(Command):
    commandId = 38

    def dataToBytes(self):
        return struct.pack('!BBBB', *map(int, self.data.split('.')))


class SetCameraIpAddress(Command):
    commandId = 40

    def dataToBytes(self):
        ipAddress = self.data['ipAddress']
        subnetMask = self.data['subnetMask']
        gateway = self.data['gateway']
        return struct.pack('!BBBBBBBBBBBB',
                           *map(int, ipAddress.split('.')),
                           *map(int, subnetMask.split('.')),
                           *map(int, gateway.split('.')))


class SetCameraMacAddress(Command):
    commandId = 41

    def dataToBytes(self):
        return struct.pack('!BBBBBB', *map(lambda x: int(x, 16), self.data.split(':')))


class SetGrayscaleIllumination(Command):
    commandId = 39


class CalibrateProduction(Command):
    commandId = 31

class SetCompensation(Command):
    commandId = 28

    def dataToBytes(self):
        return struct.pack('!BBBB',
                            self.data['setDrnuCompensationEnabed'],
                            self.data['setTemperatureCompensationEnabled'],
                            self.data['setAmbientLightCompensationEnabled'],
                            self.data['setGrayscaleCompensationEnabled'])



commands = {'setRoi': SetRoi,
            'setIntTimes': SetIntTimes,
            'getDistanceAndAmplitude': GetDistanceAndAmplitude,
            'getDistance': GetDistance,
            'getGrayscale': GetGrayscale,
            'getDcs': GetDcs,
            'stopStream': StopStream,
            'systemReset': SystemReset,
            'jumpToBootloader': JumpToBootloader,
            'powerReset': PowerReset,
            'setMinAmplitude': SetMinAmplitude,
            'setFilter': SetFilter,
            'setModulationFrequency': SetModulationFrequency,
            'setBinning': SetBinning,
            'setHdr': SetHdr,
            'readChipInformation': ReadChipInformation,
            'readFirmwareRelease': ReadFirmwareRelease,
            'setDllStep': SetDllStep,
            'writeRegister': WriteRegister,
            'readRegister': ReadRegister,
            'getTemperature': GetTemperature,
            'setDataIpAddress': SetDataIpAddress,
            'setCameraIpAddress': SetCameraIpAddress,
            'setCameraMacAddress': SetCameraMacAddress,
            'setGrayscaleIllumination': SetGrayscaleIllumination,
            'calibrateProduction': CalibrateProduction,
            'setCompensation' : SetCompensation,
            }
