"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

class Type():
  DATA_ACK                     = 0x00     # Acknowledge from sensor to host
  DATA_NACK                    = 0x01     # Not acknowledge from sensor to host
  DATA_IDENTIFICATION          = 0x02     # Identification to identify the device
  DATA_DISTANCE                = 0x03     # Distance information
  DATA_AMPLITUDE               = 0x04     # Amplitude information
  DATA_DISTANCE_AMPLITUDE      = 0x05     # Distance and amplitude information
  DATA_GRAYSCALE               = 0x06     # Grayscale information
  DATA_DCS                     = 0x07     # DCS data
  DATA_DCS_DISTANCE_AMPLITUDE  = 0x08     # DCS, distance and amplitude all together
  DATA_INTEGRATION_TIME        = 0x09     # DCS, distance and amplitude all together
  DATA_ANGLE                   = 0x0A			# TofScan current angle of steppermotor
  DATA_NBF                     = 0x0B 		# NBF data dist,ampl,degree,delta
  DATA_BRIDGE                  = 0x0b     # uart response from uart1 looped via other uart
  DATA_CALIBRATION_INFO        = 0xF6     # get calibration Data Info
  DATA_DEBUG                   = 0xF8     # DEBUG INFORMATIONS
  DATA_PRODUCTION_INFO         = 0xF9     # DCS, distance and amplitude all together
  DATA_CALIBRATION_DATA        = 0xFA     # DCS, distance and amplitude all together
  DATA_REGISTER                = 0xFB
  DATA_TEMPERATURE             = 0xFC
  DATA_CHIP_INFORMATION        = 0xFD     # Error number
  DATA_FIRMWARE_RELEASE        = 0xFE     # Error number
  DATA_ERROR                   = 0xFF     # Error number
