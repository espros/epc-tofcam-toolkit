class update():
  INDEX_CONTROL      = 2          #Index of the control byte
  INDEX_INDEX        = 3          #Index of the index
  INDEX_DATA         = 6          #Index of the update data
  CONTROL_START      = 0          #Control byte start update
  CONTROL_WRITE_DATA = 1          #Control byte write data
  CONTROL_COMPLETE   = 2          #Control byte update complete
  PASSWORD_DELETE    = 0x654321   #Password needed to prevent an accidently delete