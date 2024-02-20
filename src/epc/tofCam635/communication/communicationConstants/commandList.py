"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

class CommandList():
  # setup commands
  COMMAND_SET_INT_TIME_DIST = 0x00                      #Command to set the integration time for 3D operation
  COMMAND_SET_INTEGRATION_TIME_GRAYSCALE = 0x01               #Command to set the integration time for grayscale
  COMMAND_SET_ROI = 0x02                                      #Command to set the region of interest
  COMMAND_SET_BINNING = 0x03                                  #Command to set binning
  COMMAND_SET_OPERATION_MODE = 0x04                           #Command to set the mode
  COMMAND_SET_MODULATION_FREQUENCY = 0x05                     #Command to set the modulation frequency
  COMMAND_SET_DLL_STEP = 0x06                                 #Command to set the DLL step
  COMMAND_SET_TEMPORAL_FILTER_WFOV = 0x07                                   #Command to set the filter for the WF illumination

  COMMAND_SET_MEDIAN_FILTER = 0x08                            #Command to set the median filter
  COMMAND_SET_AMPLITUDE_LIMIT = 0x09                          #Command to set the amplitude limit
  COMMAND_SET_AVERAGE_FILTER = 0x0A                           #Command to set the average filter
  COMMAND_SET_HDR = 0x0D                                      #Command to set the HDR mode
  COMMAND_SET_MOD_CHANNEL = 0x0E                              #Command to set the Modulation channel
  COMMAND_SET_FILTER_SINGLE_SPOT = 0x0F                       #Command to set the filter for the NF spot result
  COMMAND_SET_EDGE_FILTER = 0x10                              #Command to set the edge filter
  COMMAND_SET_INTERFERENCE_DETECTION = 0x11                   #Command to set the interference detection settings

  # acquisition commands
  COMMAND_GET_DISTANCE = 0x20                                 #Command to request distance data
  COMMAND_GET_DISTANCE_AMPLITUDE = 0x22                       #Command to request distance and amplitude data
  COMMAND_GET_GRAYSCALE = 0x24                                #Command to request grayscale data
  COMMAND_GET_DCS = 0x25                                      #Command to request DCS data
  COMMAND_SET_AUTO_ACQUISITION = 0x26
  COMMAND_GET_INTEGRATION_TIME_3D = 0x27                      #Command to get the integration time for 3D operation#Command to enable/disable the auto acquisition
  COMMAND_STOP_STREAM = 0x28                                  #Command to stop the stream

  # general commands
  COMMAND_WRITE_REGISTER = 0x4C
  COMMAND_READ_REGISTER = 0x4d
  COMMAND_IDENTIFY = 0x47
  COMMAND_IDENTIFY = 0x47                                     #Command to identify
  COMMAND_GET_CHIP_INFORMATION = 0x48                         #Command to read the chip information
  COMMAND_GET_FIRMWARE_RELEASE = 0x49                         #Command to read the firmware release
  COMMAND_GET_PRODUCTION_INFO = 0x50                          #Command to read the production info in year [uint8_t] and week [uint8_t]
  COMMAND_GET_CALIBRATION_INFO  = 0x57                        #Command to get calibration info
  COMMAND_SET_REGISTER = 0x5C                                 #Command to read register
  COMMAND_GET_REGISTER = 0x5D                                 #Command to write register
  COMMAND_GET_TEMPERATURE = 0x4A                              #Command to read the temperature
  COMMAND_SYSTEM_RESET = 0x6d