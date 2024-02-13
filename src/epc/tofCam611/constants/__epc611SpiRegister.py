

"""
this class contains the registers of the epc611 chip
the registers are added when needed, so feel free to expand the list
"""
IC_TYPE           = 0x00
IC_VERSION        = 0x01
MEM_CTRL_CONF_0   = 0x02
MEM_CTRL_CONF_1   = 0x03

EE_PAGE           = 0x10
EE_ADDR           = 0x11
EE_DATA           = 0x12
EE_MASK           = 0x13
PROG_EE_REQ       = 0x14
PROT_CONF_EN_0    = 0x15
PROT_CONF_EN_1    = 0x16
EE_READ_TRIM      = 0x17
EE_READ_TIME      = 0x18
EE_WRITE_TIME     = 0x19
EE_BIST_TEST_LOOP = 0x1a
EE_TEST           = 0x1b
Strap             = 0x20

MT_0_hi           = 0x22
MT_0_mi           = 0x23
MT_0_lo           = 0x24
MT_1_hi           = 0x25
MT_1_mi           = 0x26
MT_1_lo           = 0x27
MT_2_hi           = 0x28
MT_2_mi           = 0x29
MT_2_lo           = 0x2a   
MT_3_hi           = 0x2b
MT_3_mi           = 0x2c
MT_3_lo           = 0x2d    
MT_4_hi           = 0x2e
MT_4_mi           = 0x2f
MT_4_lo           = 0x30 
MT_5_hi           = 0x31
MT_5_mi           = 0x32
MT_5_lo           = 0x33
MT_6_hi           = 0x34
MT_6_mi           = 0x35
MT_6_lo           = 0x36
MT_7_hi           = 0x37
MT_7_mi           = 0x38
MT_7_lo           = 0x39
MT_8_hi           = 0x3a
MT_8_mi           = 0x3b
MT_8_lo           = 0x3c
SR_Adress         = 0x40
SR_Data_0         = 0x41
SR_Program        = 0x47
SR_Enable_0       = 0x48
SR_Enable_1       = 0x49
SEQ_Control       = 0x91