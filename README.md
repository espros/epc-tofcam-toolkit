<div align="center">
<img src="https://raw.githubusercontent.com/espros/epc-tofcam-toolkit/master/docs/source/images/epc-logo.png" width="300">
</div>

# ESPROS TOFcam Toolkit
The ESPROS TOFcam Toolkit is designed to control and visualize ESPROS TOFcam devices.
It provides python modules for most TOFcam modules and GUI applications for interactive control and visualization.

Website: https://www.espros.com  
Products: https://www.digikey.com/en/supplier-centers/espros  
Documentation: https://docs.esprso.com/epc_tofcam_toolkit
Source code: https://github.com/espros/epc-tofcam-toolkit


<img src="https://raw.githubusercontent.com/espros/epc-tofcam-toolkit/master/docs/source/images/gui660_pointcloud.png" width="800">

## Quick-start
To install the toolkit include all necessary dependencies for the graphical user interface, install the package using the [gui] extra:
```bash
pip install "epc-tofcam-toolkit[gui]"
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

Clone this repository and cd into it.

### 1. Create and activate a virtual environment

```bash
python -m venv .venv

# linux / macOS
source .venv/bin/activate

# windows
.\.venv\Scripts\activate
```

### 2. Install modules and dependencies

All dependencies are managed using the `pyproject.toml` and installed via `pip`. Choose the install option that fits your use case:

**Option A — Core API**:

Install only the epc-tofcam-toolkit API and dependencies to control the camera.

```bash
pip install -e .
```

**Option B — Core API & Full development environment inlcuding the GUI**:
```bash
pip install --editable ".[dev,gui]"
```

Installs the full development environment and all dependency groups:

| Group | Purpose |
|-------|---------|
| `gui` | Required to run the GUI applications |
| `dev` | Required for testing and type checking |
