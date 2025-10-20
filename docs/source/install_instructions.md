# Installation

This section will guide you through the installation process of our software.

## Prerequisites

Before you begin, ensure you have met the following requirements:

* You have installed a python version equal or grater to v3.10

## Installing ESPROS TOFcam Toolkit

To install the ESPROS TOFcam Toolkit follow these steps:

1. Open your terminal.  
2. "Optional" create a [python virtual environment](https://docs.python.org/3/library/venv.html)
3. Use the package manager pip to install ESPROS TOFcam Toolkit:

```bash
pip install epc-tofcam-toolkit

```

## Run the GUIs
Since the GUI depends on a lot of bigger 3th party python packages, its installation is optional. 
```bash
pip install epc-tofcam-toolkit[gui]
```
After successfully installing the package with the commands above simple type the following commands in your terminal. 

```bash
# To run the GUI for TOFcam660
tofcam660
# To run the GUI for TOFcam635
tofcam635
# TO run the GUI for TOFcam611
tofcam611
```