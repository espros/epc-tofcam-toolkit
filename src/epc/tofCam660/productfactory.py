from epc.tofCam660.epc660 import Epc660Ethernet, Epc660Usb


class ProductFactory:
    def __init__(self):
        self.product_catalog = {'660_ethernet': Epc660Ethernet,
                                '660_usb': Epc660Usb}

    def create_product(self, producttype, revision=0):
        return self.product_catalog[producttype](revision)
