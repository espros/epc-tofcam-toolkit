
from epc.tofCam660 import TOFcam660

def test_crc():
    cam = TOFcam660()
    chip_id, wafer_id = cam.device.get_chip_infos()
    print(f"Chip_id:{chip_id}")

    dcs = cam.get_raw_dcs_images()
    is_valid = cam.get_crc_status( )
    print("DCS image CRC check passed:", is_valid)

    distance = cam.get_distance_image()
    is_valid = cam.get_crc_status()
    print("Distance image CRC check passed:", is_valid)

    distance, amplitude = cam.get_distance_and_amplitude()
    is_valid = cam.get_crc_status()
    print("Distance,Amplitude image CRC check passed:", is_valid)

test_crc()