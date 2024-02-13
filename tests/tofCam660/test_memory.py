import pytest
from epc.tofCam660 import Memory

@pytest.fixture(scope='function')
def memory():
    # create a new memory object for every test
    return Memory.create(0)

class Test_Memory():
    def test_getAddress(self, memory: Memory):
        assert 0x01 == memory.getAddress('ic_version')

    def test_iterator_protocol(self, memory: Memory):
        for registername in memory:
            pass
        assert 'ee_rd_protection' == registername