class Crc():
    """ Unlike the tofcam635, the tofcam660 usb interface does not use crc.
    In case this is going to change, the interface is kept the same for
    both cameras. """

    markerEnd = 0xcafebabe

    def calcCrc32(self, data):
        return self.markerEnd

    def isCrcCorrect(self, data, checksum):
        return self.markerEnd == checksum
