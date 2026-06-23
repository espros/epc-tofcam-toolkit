# Changelog

## [Unreleased]

## [0.10.0] - 2026-06-23

### TOFcam670 GUI
- Disable inactive settings based on acquisition modes.

### General
- improved README.md
- changed docs to common espros look
- added tofcam670 to the documentation
- Improve FPS indicator on all GUI's

## [0.9.0] - 2026-06-03
### TOFcam670
- Added interference filter
- Added edge filter

### General GUI
- Added keyboard shortcut to trigger a single capture using the Return key
- Added color scale histogram to the Point-Cloud visualization
- Added dropdown to the Point-Cloud visualization to select point coloring by distance or amplitude
- Added tool tips for filters and settings
- Removed Menu button and stripped content menu for images

## [0.8.0] - 2026-05-13
### TOFcam670
- Added support for the TOFcam670 on native Linux platforms (e.g. Raspberry Pi)

### General GUI
- Improved GUI responsiveness
- Added keyboard shortcuts for common actions
- Added unit selection menu (mm, cm, inch)
- Improved clipping behavior for data outside the selected range

## [0.7.1] - 2026-05-07
### TOFcam670
- Fix missing 24MHz setting in GUI

## [0.7.0] - 2026-05-05
### TOFcam670
- Added support for the TOFcam670 on native Linux platforms (e.g. Raspberry Pi)

### General GUI
- Improved GUI responsiveness
- Added keyboard shortcuts for common actions
- Added unit selection menu (mm, cm, inch)
- Improved clipping behavior for data outside the selected range

## [0.6.1] - 2026-04-29

### General
- use pyproject.toml for all dependency management
- improved README.md

## [0.6.0] - 2026-03-24

### TOFcam635
- added setIlluminatorSegments command

### TOFcam611
- solve pcd cloud visualization issue
- add command for setting grayscale integration time

## [0.5.1] - 2026-01-29
- Fix CI/CD pipeline for to deploy the python package to pypi

## [0.5.0] - 2026-01-28

### TOFcam660
- Adding additional ultra wide field lenses calibration data for point-cloud projection.

## [0.4.0] - 2026-01-27

### TOFcam660
- Bugfix on Ethernet interface to handle stale UDP data dn TCP timeouts
- Added the following commands for compatibility with FW version >= 
  - setHwTriggerDataType: 
  - setRollingMode: Enable Rolling Mode for Data Acquisition
  - setEyeSafety: 
  - setModClkJitter: Enable/Disable Modulation Clock Jitter

## [0.3.2] - 2025-11-24

### TOFcam660
- Fix: Only load calibration data when necessary

## [0.3.1] - 2025-11-24
- Fix: Dependencies

## [0.3.0] - 2025-11-07

### TOFcam660
- Add flexible modulation frequency
- Add command for controlling illumination segments
- Add readout of calibration data
- Add saturation detection

## [0.2.0] - 2025-10-21

### TOFcam660
- Added optional TCP interface for image transmission

### GUI's
- Implemented record and playback functionality into the GUI's
- Pointcloud is now colored with signal amplitude instead of distance value

### General
- Added support for ieee crc32
- Performance improvements and bugfixes

## [0.1.1] - 2024-12-18

### GUI's
- Fix incompatibilities between pyqtdarktheme and pyside6

### General
- Fix incompatibilities with numpy>=2.0.0

## [0.1.0] - 2024-03-19

