"""
* Copyright (C) 2019 Espros Photonics Corporation
*
"""

class Identification():
  # Refer datasheets for details on the identification values
  IDENT_TOFRANGE611 = 1              #Identification for TofRange611
  IDENT_TOFFRAME611 = 2              #Identification for TofFrame611
  IDENT_TOFCAM635 = 0                #Identification for TofCam635
  VALUE_BOOTLOADER = 0x80000000      #Or this value with the identification in the bootloader
  VALUE_APPLICATION = 0x00000000     #Or this value with the identification in the application