# Changelog

## [Unreleased]
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

