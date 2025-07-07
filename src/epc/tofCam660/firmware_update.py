from epc.tofCam660 import TOFcam660
import requests
import time
import os
import logging

logger = logging.getLogger("update_firmware")

def __erase_application(base_url: str):
    erase_url = f"{base_url}/webpage.html"
    erase_params = {
        "e": "Erase-Application",
        "c1": "TOFcam-660"
    }
    logger.info("Erasing application...")
    erase_response = requests.get(erase_url, params=erase_params)
    logger.info("Erase response:", erase_response.status_code)

def __upload_firmware_file(file: str, base_url: str):
    upload_url = f"{base_url}/0S.bin"
    with open(file, "rb") as f:
        files = {"datafile": (os.path.basename(file), f, 'application/octet-stream')}
        headers = {
            'Expect': ''  # Disable problematic 'Expect: 100-continue'
        }
        logger.info("Uploading file...", files)
        upload_response = requests.post(upload_url, files=files, headers=headers, timeout=5)
        logger.info("Upload response:", upload_response.status_code)
    logger.info("FW upload completed.")

def update_firmware(tof_cam: TOFcam660, file: str):
    ip_address = tof_cam.tcpInterface.ip_address
    base_url = f"http://{ip_address}"

    # Initialize the TOFcam660 interface
    act_fw_versioni = tof_cam.device.get_fw_version()
    logger.warning(f"Performing firmware update for TOFcam660 at {ip_address} with file {file}")
    logger.info(f"Current firmware version: {act_fw_versioni}")
    logger.info("Enter Bootloader mode...")
    tof_cam.device.jump_to_bootloader()
    time.sleep(3) # Wait for the device to enter bootloader mode
    logger.info("TOFcam660 now in bootloader mode.")

    # Upload the firmware file
    try:
        __erase_application(base_url)
        __upload_firmware_file(file, base_url)
    except Exception as e:
        logger.error(f"Error during firmware update: {e}")
        logger.warning(f"Firmware update failed."
                        "Manually restart the device to exit bootloader mode"
                        "or update manually by accessing the device's web interface at {base_url}")
        exit(1)

    logger.info("Waiting for the device to reboot...")
    tof_cam.tcpInterface.close()  # Close the connection to the device
    time.sleep(2)  # Wait for the device to reboot
    tof_cam.tcpInterface.connect()  # Reconnect to the device after firmware update
    new_fw_version = tof_cam.device.get_fw_version()
    logger.info(f"New firmware version: {new_fw_version}")
    logger.info("Firmware update process completed successfully.")


if __name__ == "__main__":
    FW_BINARY = "/home/ake/Downloads/cameraApplication_XiP_3v36.bin"  # Change this to your file path
    IP_ADDRESS = "10.10.31.180"

    cam = TOFcam660(ip_address=IP_ADDRESS)

    update_firmware(cam, FW_BINARY)