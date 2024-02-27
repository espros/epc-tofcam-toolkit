from epc.tofCam_lib.crc import Crc, CrcMode

class Test_WithLib:
    def test_crcCalculation(self):
        crc = Crc(mode=CrcMode.CRC32_UINT8_LIB, revout=True)
        crc = crc.calculate(bytearray([0xFA, 0x01, 0x00, 0x00]))
        crc_exp = 0xDAD76A85

        assert crc == crc_exp

    def test_crcVerify(self):
        crc = Crc(mode=CrcMode.CRC32_UINT8_LIB, revout=True)
        assert crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00]), [0x85, 0x6A, 0xD7, 0xDA])

        assert not crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00]), [0x85, 0x6A, 0xD7, 0xDB])

class Test_WithoutLib:
    def test_crcCalculation(self):
        crc = Crc(mode=CrcMode.CRC32_UINT8, revout=True)
        crc = crc.calculate([0xFA, 0x01, 0x00, 0x00])
        crc_exp = 0xDAD76A85

        assert crc == crc_exp

    def test_crcVerify(self):
        crc = Crc(mode=CrcMode.CRC32_UINT8, revout=True)
        assert crc.verify(bytearray([0xFA, 0x01, 0x00, 0x00]), [0x85, 0x6A, 0xD7, 0xDA])

        assert not crc.verify([0xFA, 0x01, 0x00, 0x00], bytearray([0x85, 0x6A, 0xD7, 0xDB]))
