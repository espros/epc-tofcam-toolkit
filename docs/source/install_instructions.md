# Installation

This section will guide you through the installation process of our software.

## Prerequisites

Before you begin, ensure you have met the following requirements:

* You have installed a python version equal or greater to v3.10

## Installing ESPROS TOFcam Toolkit

To install the ESPROS TOFcam Toolkit follow these steps:

1. Open a terminal.  
2. Optionally create a [python virtual environment](https://docs.python.org/3/library/venv.html)
3. Use the package manager pip to install ESPROS TOFcam Toolkit:

```bash
pip install epc-tofcam-toolkit

```

## Run the GUIs
Since the GUI depends on several large 3rd party python packages, its installation is optional. 
```bash
pip install epc-tofcam-toolkit[gui]
```
After successfully installing the package with the commands above simple enter the following commands in your terminal. 

```bash
# To run the GUI for TOFcam670
tofcam670
# To run the GUI for TOFcam660
tofcam660
# To run the GUI for TOFcam635
tofcam635
# To run the GUI for TOFcam611
tofcam611
# To run the GUI for Hawkeye
hawkeye
```