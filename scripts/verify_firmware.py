import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'epc_lib')

from epc.tofCam660 import TOFcam660
import requests
import time
import os

IP_ADDRESS = "10.10.31.170"
PASSWORD = "TOFcam-660"
FW_BINARY = "scripts/cameraApplication_XiP_3v43.bin"  # Change this to your file path

def verify_firmware(ip_address: str, file: str):
    tof_cam = TOFcam660(ip_address=ip_address)
    fw_version = tof_cam.device.get_fw_version()

    fw_binary = FW_BINARY[-8:-4]

    # Convert both to (major, minor) tuple
    binary_parts = tuple(fw_binary.replace('v', '.').split('.'))
    version_parts = tuple(fw_version.split('.'))

    # Compare major and minor parts
    if binary_parts == version_parts:
        print("Firmware versions match!")
    else:
        print("ATTENTION !!!! Firmware versions do not match.")

    print("Current firmware version:", fw_version)


def update_firmware(ip_address: str, file: str):
    base_url = f"http://{ip_address}"

    # Initialize the TOFcam660 interface
    print("Initializing TOFcam660 interface...")
    tof_cam = TOFcam660(ip_address=ip_address)
    print("Enter Bootloader mode...")
    tof_cam.device.jump_to_bootloader()
    time.sleep(3) # Wait for the device to enter bootloader mode
    print("TOFcam660 now in bootloader mode.")

    # Erase Application (GET request)
    erase_url = f"{base_url}/webpage.html"
    erase_params = {
        "e": "Erase-Application",
        "c1": PASSWORD
    }
    print("Erasing application...")
    erase_response = requests.get(erase_url, params=erase_params)
    print("Erase response:", erase_response.status_code)

    time.sleep(1)  # Wait for the device to erase the application

    # Upload file (POST request)
    upload_url = f"{base_url}/0S.bin"
    with open(file, "rb") as f:
        files = {"datafile": (os.path.basename(file), f, 'application/octet-stream')}
        headers = {
            'Expect': ''  # Disable problematic 'Expect: 100-continue'
        }
        print("Uploading file...", files)
        upload_response = requests.post(upload_url, files=files, headers=headers, timeout=5)
        print("Upload response:", upload_response.status_code)

if __name__ == "__main__":
    for i in range(170, 180):
        ip = f"10.10.31.{i}"
        print(f"Starting firmware update for {ip} using file {FW_BINARY}...")
        verify_firmware(ip, FW_BINARY)
        print("Firmware update process completed.")