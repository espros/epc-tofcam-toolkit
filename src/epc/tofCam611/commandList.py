class commandList():
  # setup commands
  COMMAND_SET_INTEGRATION_TIME_3D = 0x00                      #Command to set the integration time for 3D operation
  COMMAND_SET_INTEGRATION_TIMER_GRAYSCALE = 0x01              #Command to set the integration time for grayscale
  COMMAND_SET_ROI = 0x02                                      #Command to set the region of interest
  COMMAND_SET_BINNING = 0x03                                  #Command to set the binning
  COMMAND_SET_MODE = 0x04                                     #Command to set the mode
  COMMAND_SET_MODULATION_FREQUENCY = 0x05                     #Command to set the modulation frequency
  COMMAND_SET_DLL_STEP = 0x06                                 #Command to set the DLL step
  COMMAND_SET_FILTER = 0x07                                 #Command to set the DLL step
  COMMAND_SET_RPM     = 0x08
  # acquisition commands
  COMMAND_GET_DISTANCE = 0x20                                 #Command to request distance data
  COMMAND_GET_AMPLITUDE = 0x21                                #Command to request amplitude data
  COMMAND_GET_DISTANCE_AMPLITUDE = 0x22                       #Command to request distance and amplitude data
  COMMAND_GET_DCS_DISTANCE_AMPLITUDE = 0x23                   #Command to request distance, amplitude and DCS data at once
  COMMAND_GET_GRAYSCALE = 0x24                                #Command to request grayscale data
  COMMAND_GET_DCS = 0x25                                      #Command to request DCS data
  COMMAND_SET_AUTO_ACQUISITION = 0x26
  COMMAND_GET_INTEGRATION_TIME_3D = 0x27                      #Command to get the integration time for 3D operation#Command to enable/disable the auto acquisition
  COMMAND_GET_NBF = 0x29
  # general commands
  COMMAND_SET_POWER = 0x40                                    #Command to enable/disable the power
  COMMAND_CALIBRATE_DRNU = 0x41                               #Command to start DRNU calibration
  COMMAND_CALILBRATE_OFFSET = 0x42                            #Command to calibrate the system offset
  COMMAND_GET_CALIBRATION = 0x43                              #Command to read back the calibration for backup/restore
  COMMAND_JUMP_TO_BOOTLOADER = 0x44                           #Command for application to jump to bootloader
  COMMAND_UPDATE_FIRMWARE = 0x45                              #Command to update the firmware
  COMMAND_IDENTIFY = 0x47                                     #Command to identify
  COMMAND_GET_CHIP_INFORMATION = 0x48                         #Command to read the chip information
  COMMAND_GET_FIRMWARE_RELEASE = 0x49                         #Command to read the firmware release
  COMMAND_GET_TEMPERATURE = 0x4A
  COMMAND_WRITE_CALIBRATION_DATA = 0x4B
  COMMAND_WRITE_REGISTER = 0x4C
  COMMAND_READ_REGISTER = 0x4D
  COMMAND_NOP = 0x4E
  COMMAND_GET_PRODUCTION_INFO = 0x50                         #Command to read the production info in year [uint8_t] and week [uint8_t]
  COMMAND_SET_0_DEGREE_MARK = 0x51                          #Command to send zero degree mark for tofscan
  COMMAND_SET_DOUBLE_BUFFER = 0x52                         #Command to  enable double buffer mode on evalkit
  COMMAND_GET_ERROR = 0x53                               #Command to  enable double buffer mode on evalkit
  COMMAND_GET_DEBUG = 0xA0                                 #<Command to read the debug information

  COMMAND_SET_EXTERNAL_DELAY_LINE = 0x80;                     # Command to set external delay line in ps [uint32_t]
  COMMAND_WRITE_CONFIGURATION = 0x81;                       # Command write the hw configuration to the flash
