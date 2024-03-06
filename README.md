# EPC TOFCam python package
This repository contains the python GUI framework for TOF cameras.

## Installation for usage
install the package using pip
```bash
pip install epc-tofcam-toolkit
```

Connect and startup the camera. Then simply run the gui with: 
```bash 
epc-tofcam660
epc-tofcam635
epc-tofcam611
```
- TOFcam660 will try to connect to ip-address 10.10.31.180
- TOFcam635 will try to find the com port automatically
- TOFcam611 will try to find the com port automatically

You can also manually specify the communication port
```bash 
epc-tofcam660 --ip 10.10.31.180
epc-tofcam635 --port COM3
epc-tofcam611 --port COM3
```

## Installation for development

Clone this repository 
```bash
git clone git@gitlab.ch.epc:MOD/02_Applications/EPC-TOFcam-GUI.git
```

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

## Repository structure

The repository is structured as follows:

Folder          | Content
----------------| ---------------------------------
doc             | Sphinx documentation and data-sheets for this project
src             | All python packages
tests           | Tests for packages in src


# GUI Main Structure
The gui structure locks like in the following class diagram.  
![GUI_Class_diagram](doc/source/images/GUI_Class_diagram.png)

Class Type      | Description
--------------- | ----------------------------------------
Base GUI        | This is the base class all guis derive from. It defines common widgets, like the task bar and the image view.
GUI_TOFcamXXX   | These classes implement the guis for each camera. No reference to the camera lib shall be implemented here.
TOFcamXXX_bridge | The Bridge classes function as bridge between the GUI and the underlying TOFcamXXX library. The are responsible to connect the gui to the camera. No GUI Widgets shall be added here. 
TOFcamXXX       | These are the actual TOFcamXXX libraries for each camera
