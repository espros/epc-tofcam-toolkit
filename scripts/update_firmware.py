from epc.tofCam660 import TOFcam660
import requests
import time
import os

IP_ADDRESS = "10.10.31.170"
PASSWORD = "TOFcam-660"
FW_BINARY = "scripts/cameraApplication_XiP_3v39.bin"  # Change this to your file path

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
    for i in range(175, 179):
        ip = f"10.10.31.{i}"
        print(f"Starting firmware update for {ip} using file {FW_BINARY}...")
        update_firmware(ip, FW_BINARY)
        print("Firmware update process completed.")