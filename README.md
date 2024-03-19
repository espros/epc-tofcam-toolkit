<div align="center">
<img src="https://raw.githubusercontent.com/espros/epc-tofcam-toolkit/master/docs/source/images/epc-logo.png" width="300">
</div>

# ESPROS TOFcam Toolkit
The ESPROS TOFcam Toolkit is designed to control and visualize ESPROS TOFcam devices.
It provides python modules for most TOFcam modules and GUI applications for interactive control and visualization.

Website: https://www.espros.com  
Products: https://www.digikey.com/en/supplier-centers/espros  
Documentation: https://epc-tofcam-toolkit.readthedocs.io/en/latest/  
Source code: https://github.com/espros/epc-tofcam-toolkit


<img src="https://raw.githubusercontent.com/espros/epc-tofcam-toolkit/master/docs/source/images/gui660_pointcloud.png" width="800">

## Quick-start
install the package using pip
```bash
pip install epc-tofcam-toolkit
```

Connect and startup the camera. Then simply run the gui with: 
```bash 
tofcam660
tofcam635
tofcam611
tofrange611
```
- TOFcam660 will try to connect to ip-address 10.10.31.180
- TOFcam635 will try to find the com port automatically
- TOFcam611 will try to find the com port automatically

You can also manually specify the communication port
```bash 
tofcam660 --ip 10.10.31.180
tofcam635 --port COM3
tofcam611 --port COM3
tofrange611 --port COM3
```

## Installation for development

Clone this repository and cd into it

Create a virtual environment and activate it
```bash
python -m venv .venv  

# linux
source .venv/bin/activate

# windows
.\.venv\Scripts\activate
```

Install the package in editable mode
```bash
pip install -e .
```