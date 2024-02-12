# EPC TOFCam python package
This folder contains the python framework for the TOFCAM660.
It allows communication with the camera via ethernet and usb connection.

For USB connections on windows it may be necessary to set the USB port manually.  
This can be done at the top of the usb_interface.py file.  
Parameters for the ethernet connection can be changed in trace_interface.py.  

The server.py file contains most of the functionality, including all implemented commands.  

Examples on how to establish a connection, and use these commands are provided in the examples folder.  


## Installation for development

Clone this repository 
```bash
git clone git@gitlab.ch.epc:MOD/06_Utilities/eye_safety_calculations.git
```

Create a virtual environment and activate it
```bash
python -m venv .venv  
source .venv/bin/activate
```

Install the package in editable mode
```bash
pip install -e .
```

## Repository structure

The repository is structured as follows:

Folder          | Content
----------------| ---------------------------------
doc             | Sphinx documentation and data-sheets for this project
src             | All python packages
tests           | Tests for packages in src
