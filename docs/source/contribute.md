# Installation for development

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
