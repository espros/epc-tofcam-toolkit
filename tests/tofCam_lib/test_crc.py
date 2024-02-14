from epc.tofCam_lib import Crc

class Test_WithLib:
    def test_crcCalculation(self):
        crc = Crc(revout=True, useLib=True)
        crc = crc.calcCrc32Uint8(bytearray([0xFA, 0x01, 0x00, 0x00]))
        crc_exp = 0xDAD76A85

        assert crc == crc_exp

    def test_crcVerify(self):
        crc = Crc(revout=True, useLib=True)
        assert crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00, 0x85, 0x6A, 0xD7, 0xDA]))

        assert not crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00, 0x85, 0x6A, 0xD7, 0xDB]))

class Test_WithoutLib:
    def test_crcCalculation(self):
        crc = Crc(revout=True, useLib=False)
        crc = crc.calcCrc32Uint8(bytearray([0xFA, 0x01, 0x00, 0x00]))
        crc_exp = 0xDAD76A85

        assert crc == crc_exp

    def test_crcVerify(self):
        crc = Crc(revout=True, useLib=False)
        assert crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00, 0x85, 0x6A, 0xD7, 0xDA]))

        assert not crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00, 0x85, 0x6A, 0xD7, 0xDB]))
