import struct


class Response:
    """Use factory method 'create(responseId, ...)' to instantiate"""
    data = None

    @staticmethod
    def fromBytes(payload):
        responseId = struct.unpack('!B', payload[:1])[0]
        data = payload[1:]
        try:
            return responses[responseId](data)
        except KeyError:
            raise ValueError('there is no response {}'.format(responseId))

    def __init__(self, data):
        self.parseDataFromBytes(data)

    def parseDataFromBytes(self, data):
        """overwrite me to implement different byte arrangement of data"""
        self.data = data

    def __repr__(self):
        if not self.data == None:
            try:
                dataString = ', '.join(['0x{:02x}'.format(entry) for entry in self.data])
            except TypeError:
                dataString = hex(self.data)
            except ValueError:
                dataString = str(self.data)
        else:
            dataString = ''
        return 'response: {}, data: [{}]'.format(self.__class__.__name__, dataString)

    def isError(self):
        return False


class Acknowledge(Response):
    pass


class Error(Response):
    def parseDataFromBytes(self, data):
        self.data = struct.unpack('!H', data)[0]

    def isError(self):
        return True


class FirmwareRelease(Response):
    def parseDataFromBytes(self, data):
        major, minor = struct.unpack('!HH', data)
        self.data = {'major': major,
                     'minor': minor}


class ChipInformation(Response):
    def parseDataFromBytes(self, data):
        waferid, chipid = struct.unpack('!HH', data)
        self.data = {'waferid': waferid,
                     'chipid': chipid}


class Temperature(Response):
    def parseDataFromBytes(self, data):
        self.data = struct.unpack('!h', data)[0] / 100


class ReadRegister(Response):
    def parseDataFromBytes(self, data):
        self.data = struct.unpack('!B', data)[0]


class Calibrating(Response):
    pass


class NotAcknowledge(Response):
    def isError(self):
        return True


responses = {0: Acknowledge,
             1: Error,
             2: FirmwareRelease,
             3: ChipInformation,
             4: Temperature,
             6: ReadRegister,
             254: Calibrating,
             255: NotAcknowledge, }
