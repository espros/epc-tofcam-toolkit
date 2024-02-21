# EPC TOFCam python package
This folder contains the python framework for the TOFCAM660.
It allows communication with the camera via ethernet and usb connection.

For USB connections on windows it may be necessary to set the USB port manually.  
This can be done at the top of the usb_interface.py file.  
Parameters for the ethernet connection can be changed in trace_interface.py.  

The server.py file contains most of the functionality, including all implemented commands.  

Examples on how to establish a connection, and use these commands are provided in the examples folder.  

## Installation for usage
install the package using pip
```bash
pip install epc-tofcam
```

Connect and startup the camera. Them simply run the gui with: 
```bash 
epc-tofcam660 --ip 10.10.31.180
```
If the camera has ip 10.10.31.180 you can evan skip the --ip flag

## Installation for development

Clone this repository 
```bash
git clone git@gitlab.ch.epc:MOD/06_Utilities/eye_safety_calculations.git
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