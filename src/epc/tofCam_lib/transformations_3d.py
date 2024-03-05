import numpy as np
import math
import cv2

#FOV=1 for WIDE FIELD, FOV=2 FOR NARROW FIELD, FOV=3 FOR STANDARD FIELD, FOV=4 For STANDARD FIELD (with NAOTECH lens)
class Transformation3D():

    def __init__(self,FOV=4,width=320,height=240,offsetX=0,offsetY=0):
        self.angle=np.zeros(101)
        self.rp=np.zeros(101)
        self.height=height
        self.width=width
        self.xUA=np.zeros((self.width,self.height))
        self.yUA=np.zeros((self.width,self.height))
        self.zUA=np.zeros((self.width,self.height))


        if(FOV==1):
            self.angle[0]  = 0.0
            self.angle[1]  = 0.742
            self.angle[2]  = 1.483
            self.angle[3]  = 2.225
            self.angle[4]  = 2.967
            self.angle[5]  = 3.708
            self.angle[6]  = 4.45
            self.angle[7]  = 5.192
            self.angle[8]  = 5.933
            self.angle[9]  = 6.675
            self.angle[10] = 7.417
            self.angle[11] = 8.158
            self.angle[12] = 8.9
            self.angle[13] = 9.642
            self.angle[14] = 10.384
            self.angle[15] = 11.125
            self.angle[16] = 11.867
            self.angle[17] = 12.609
            self.angle[18] = 13.35
            self.angle[19] = 14.092
            self.angle[20] = 14.834
            self.angle[21] = 15.575
            self.angle[22] = 16.317
            self.angle[23] = 17.059
            self.angle[24] = 17.8
            self.angle[25] = 18.542
            self.angle[26] = 19.284
            self.angle[27] = 20.025
            self.angle[28] = 20.767
            self.angle[29] = 21.509
            self.angle[30] = 22.25
            self.angle[31] = 22.992
            self.angle[32] = 23.734
            self.angle[33] = 24.475
            self.angle[34] = 25.217
            self.angle[35] = 25.959
            self.angle[36] = 26.701
            self.angle[37] = 27.442
            self.angle[38] = 28.184
            self.angle[39] = 28.926
            self.angle[40] = 29.667
            self.angle[41] = 30.409
            self.angle[42] = 31.151
            self.angle[43] = 31.892
            self.angle[44] = 32.634
            self.angle[45] = 33.376
            self.angle[46] = 34.117
            self.angle[47] = 34.859
            self.angle[48] = 35.601
            self.angle[49] = 36.342
            self.angle[50] = 37.084
            self.angle[51] = 37.826
            self.angle[52] = 38.567
            self.angle[53] = 39.309
            self.angle[54] = 40.051
            self.angle[55] = 40.792
            self.angle[56] = 41.534
            self.angle[57] = 42.276
            self.angle[58] = 43.018
            self.angle[59] = 43.759
            self.angle[60] = 44.501
            self.angle[61] = 45.243
            self.angle[62] = 45.984
            self.angle[63] = 46.726
            self.angle[64] = 47.468
            self.angle[65] = 48.209
            self.angle[66] = 48.951
            self.angle[67] = 49.693
            self.angle[68] = 50.434
            self.angle[69] = 51.176
            self.angle[70] = 51.918
            self.angle[71] = 52.659
            self.angle[72] = 53.401
            self.angle[73] = 54.143
            self.angle[74] = 54.884
            self.angle[75] = 55.626
            self.angle[76] = 56.368
            self.angle[77] = 57.109
            self.angle[78] = 57.851
            self.angle[79] = 58.593
            self.angle[80] = 59.335
            self.angle[81] = 60.076
            self.angle[82] = 60.818
            self.angle[83] = 61.56
            self.angle[84] = 62.301
            self.angle[85] = 63.043
            self.angle[86] = 63.785
            self.angle[87] = 64.526
            self.angle[88] = 65.268
            self.angle[89] = 66.01
            self.angle[90] = 66.751
            self.angle[91] = 67.493
            self.angle[92] = 68.235
            self.angle[93] = 68.976
            self.angle[94] = 69.718
            self.angle[95] = 70.46
            self.angle[96] = 71.201
            self.angle[97] = 71.943
            self.angle[98] = 72.685
            self.angle[99] = 73.426
            self.angle[100] = 74.168

            #size mm
            self.rp[0] = 0.0
            self.rp[1] = 0.048
            self.rp[2] = 0.095
            self.rp[3] = 0.143
            self.rp[4] = 0.19
            self.rp[5] = 0.238
            self.rp[6] = 0.286
            self.rp[7] = 0.333
            self.rp[8] = 0.381
            self.rp[9] = 0.428
            self.rp[10] = 0.476
            self.rp[11] = 0.523
            self.rp[12] = 0.571
            self.rp[13] = 0.618
            self.rp[14] = 0.665
            self.rp[15] = 0.713
            self.rp[16] = 0.76
            self.rp[17] = 0.807
            self.rp[18] = 0.854
            self.rp[19] = 0.901
            self.rp[20] = 0.948
            self.rp[21] = 0.995
            self.rp[22] = 1.042
            self.rp[23] = 1.089
            self.rp[24] = 1.135
            self.rp[25] = 1.182
            self.rp[26] = 1.228
            self.rp[27] = 1.275
            self.rp[28] = 1.321
            self.rp[29] = 1.367
            self.rp[30] = 1.413
            self.rp[31] = 1.459
            self.rp[32] = 1.505
            self.rp[33] = 1.551
            self.rp[34] = 1.596
            self.rp[35] = 1.641
            self.rp[36] = 1.687
            self.rp[37] = 1.732
            self.rp[38] = 1.777
            self.rp[39] = 1.822
            self.rp[40] = 1.866
            self.rp[41] = 1.911
            self.rp[42] = 1.955
            self.rp[43] = 1.999
            self.rp[44] = 2.043
            self.rp[45] = 2.087
            self.rp[46] = 2.13
            self.rp[47] = 2.173
            self.rp[48] = 2.216
            self.rp[49] = 2.259
            self.rp[50] = 2.302
            self.rp[51] = 2.344
            self.rp[52] = 2.386
            self.rp[53] = 2.428
            self.rp[54] = 2.47
            self.rp[55] = 2.511
            self.rp[56] = 2.552
            self.rp[57] = 2.593
            self.rp[58] = 2.634
            self.rp[59] = 2.674
            self.rp[60] = 2.714
            self.rp[61] = 2.754
            self.rp[62] = 2.793
            self.rp[63] = 2.832
            self.rp[64] = 2.871
            self.rp[65] = 2.909
            self.rp[66] = 2.948
            self.rp[67] = 2.985
            self.rp[68] = 3.023
            self.rp[69] = 3.06
            self.rp[70] = 3.096
            self.rp[71] = 3.132
            self.rp[72] = 3.168
            self.rp[73] = 3.204
            self.rp[74] = 3.239
            self.rp[75] = 3.273
            self.rp[76] = 3.308
            self.rp[77] = 3.341
            self.rp[78] = 3.375
            self.rp[79] = 3.408
            self.rp[80] = 3.44
            self.rp[81] = 3.472
            self.rp[82] = 3.504
            self.rp[83] = 3.535
            self.rp[84] = 3.565
            self.rp[85] = 3.595
            self.rp[86] = 3.625
            self.rp[87] = 3.654
            self.rp[88] = 3.682
            self.rp[89] = 3.71
            self.rp[90] = 3.738
            self.rp[91] = 3.765
            self.rp[92] = 3.791
            self.rp[93] = 3.817
            self.rp[94] = 3.842
            self.rp[95] = 3.866
            self.rp[96] = 3.89
            self.rp[97] = 3.914
            self.rp[98] = 3.936
            self.rp[99] = 3.959
            self.rp[100] = 3.98

        if(FOV==2):

            self.angle[0] = 0.00
            self.angle[1] = 0.19
            self.angle[2] = 0.38
            self.angle[3] = 0.57
            self.angle[4] = 0.76
            self.angle[5] = 0.95
            self.angle[6] = 1.14
            self.angle[7] = 1.33
            self.angle[8] = 1.52
            self.angle[9] = 1.71
            self.angle[10] = 1.90
            self.angle[11] = 2.09
            self.angle[12] = 2.28
            self.angle[13] = 2.47
            self.angle[14] = 2.66
            self.angle[15] = 2.85
            self.angle[16] = 3.04
            self.angle[17] = 3.23
            self.angle[18] = 3.42
            self.angle[19] = 3.61
            self.angle[20] = 3.80
            self.angle[21] = 3.99
            self.angle[22] = 4.18
            self.angle[23] = 4.37
            self.angle[24] = 4.56
            self.angle[25] = 4.75
            self.angle[26] = 4.94
            self.angle[27] = 5.13
            self.angle[28] = 5.33
            self.angle[29] = 5.52
            self.angle[30] = 5.71
            self.angle[31] = 5.90
            self.angle[32] = 6.09
            self.angle[33] = 6.28
            self.angle[34] = 6.47
            self.angle[35] = 6.66
            self.angle[36] = 6.85
            self.angle[37] = 7.04
            self.angle[38] = 7.23
            self.angle[39] = 7.42
            self.angle[40] = 7.61
            self.angle[41] = 7.80
            self.angle[42] = 7.99
            self.angle[43] = 8.18
            self.angle[44] = 8.37
            self.angle[45] = 8.56
            self.angle[46] = 8.75
            self.angle[47] = 8.94
            self.angle[48] = 9.13
            self.angle[49] = 9.32
            self.angle[50] = 9.51
            self.angle[51] = 9.70
            self.angle[52] = 9.89
            self.angle[53] = 10.08
            self.angle[54] = 10.27
            self.angle[55] = 10.46
            self.angle[56] = 10.65
            self.angle[57] = 10.84
            self.angle[58] = 11.03
            self.angle[59] = 11.22
            self.angle[60] = 11.41
            self.angle[61] = 11.60
            self.angle[62] = 11.79
            self.angle[63] = 11.98
            self.angle[64] = 12.17
            self.angle[65] = 12.36
            self.angle[66] = 12.55
            self.angle[67] = 12.74
            self.angle[68] = 12.93
            self.angle[69] = 13.12
            self.angle[70] = 13.31
            self.angle[71] = 13.50
            self.angle[72] = 13.69
            self.angle[73] = 13.88
            self.angle[74] = 14.07
            self.angle[75] = 14.26
            self.angle[76] = 14.45
            self.angle[77] = 14.64
            self.angle[78] = 14.83
            self.angle[79] = 15.02
            self.angle[80] = 15.21
            self.angle[81] = 15.40
            self.angle[82] = 15.59
            self.angle[83] = 15.79
            self.angle[84] = 15.98
            self.angle[85] = 16.17
            self.angle[86] = 16.36
            self.angle[87] = 16.55
            self.angle[88] = 16.74
            self.angle[89] = 16.93
            self.angle[90] = 17.12
            self.angle[91] = 17.31
            self.angle[92] = 17.50
            self.angle[93] = 17.69
            self.angle[94] = 17.88
            self.angle[95] = 18.07
            self.angle[96] = 18.26
            self.angle[97] = 18.45
            self.angle[98] = 18.64
            self.angle[99] = 18.83
            self.angle[100] = 19.02

            #Real
            self.rp[0] = 0.0
            self.rp[1] = 0.04
            self.rp[2] = 0.08
            self.rp[3] = 0.11
            self.rp[4] = 0.15
            self.rp[5] = 0.19
            self.rp[6] = 0.23
            self.rp[7] = 0.26
            self.rp[8] = 0.30
            self.rp[9] = 0.34
            self.rp[10] = 0.38
            self.rp[11] = 0.41
            self.rp[12] = 0.45
            self.rp[13] = 0.49
            self.rp[14] = 0.53
            self.rp[15] = 0.57
            self.rp[16] = 0.60
            self.rp[17] = 0.64
            self.rp[18] = 0.68
            self.rp[19] = 0.72
            self.rp[20] = 0.75
            self.rp[21] = 0.79
            self.rp[22] = 0.83
            self.rp[23] = 0.87
            self.rp[24] = 0.91
            self.rp[25] = 0.94
            self.rp[26] = 0.98
            self.rp[27] = 1.02
            self.rp[28] = 1.06
            self.rp[29] = 1.10
            self.rp[30] = 1.13
            self.rp[31] = 1.17
            self.rp[32] = 1.21
            self.rp[33] = 1.25
            self.rp[34] = 1.29
            self.rp[35] = 1.33
            self.rp[36] = 1.36
            self.rp[37] = 1.40
            self.rp[38] = 1.44
            self.rp[39] = 1.48
            self.rp[40] = 1.52
            self.rp[41] = 1.56
            self.rp[42] = 1.60
            self.rp[43] = 1.63
            self.rp[44] = 1.67
            self.rp[45] = 1.71
            self.rp[46] = 1.75
            self.rp[47] = 1.79
            self.rp[48] = 1.83
            self.rp[49] = 1.87
            self.rp[50] = 1.91
            self.rp[51] = 1.95
            self.rp[52] = 1.99
            self.rp[53] = 2.02
            self.rp[54] = 2.06
            self.rp[55] = 2.10
            self.rp[56] = 2.14
            self.rp[57] = 2.18
            self.rp[58] = 2.22
            self.rp[59] = 2.26
            self.rp[60] = 2.30
            self.rp[61] = 2.34
            self.rp[62] = 2.38
            self.rp[63] = 2.42
            self.rp[64] = 2.46
            self.rp[65] = 2.50
            self.rp[66] = 2.54
            self.rp[67] = 2.58
            self.rp[68] = 2.62
            self.rp[69] = 2.66
            self.rp[70] = 2.70
            self.rp[71] = 2.74
            self.rp[72] = 2.79
            self.rp[73] = 2.83
            self.rp[74] = 2.87
            self.rp[75] = 2.91
            self.rp[76] = 2.95
            self.rp[77] = 2.99
            self.rp[78] = 3.03
            self.rp[79] = 3.08
            self.rp[80] = 3.12
            self.rp[81] = 3.16
            self.rp[82] = 3.20
            self.rp[83] = 3.24
            self.rp[84] = 3.29
            self.rp[85] = 3.33
            self.rp[86] = 3.37
            self.rp[87] = 3.42
            self.rp[88] = 3.46
            self.rp[89] = 3.50
            self.rp[90] = 3.55
            self.rp[91] = 3.59
            self.rp[92] = 3.63
            self.rp[93] = 3.68
            self.rp[94] = 3.72
            self.rp[95] = 3.77
            self.rp[96] = 3.81
            self.rp[97] = 3.85
            self.rp[98] = 3.90
            self.rp[99] = 3.94
            self.rp[100] = 3.99

        if(FOV==3):
            self.angle[0]  = 0.00
            self.angle[1]  = 0.41
            self.angle[2]  = 0.82
            self.angle[3]  = 1.24
            self.angle[4]  = 1.65
            self.angle[5]  = 2.06
            self.angle[6]  = 2.47
            self.angle[7]  = 2.89
            self.angle[8]  = 3.30
            self.angle[9]  = 3.71
            self.angle[10] = 4.12
            self.angle[11] = 4.54
            self.angle[12] = 4.95
            self.angle[13] = 5.36
            self.angle[14] = 5.77
            self.angle[15] = 6.19
            self.angle[16] = 6.60
            self.angle[17] = 7.01
            self.angle[18] = 7.42
            self.angle[19] = 7.84
            self.angle[20] = 8.25
            self.angle[21] = 8.66
            self.angle[22] = 9.07
            self.angle[23] = 9.49
            self.angle[24] = 9.90
            self.angle[25] = 10.31
            self.angle[26] = 10.72
            self.angle[27] = 11.13
            self.angle[28] = 11.55
            self.angle[29] = 11.96
            self.angle[30] = 12.37
            self.angle[31] = 12.78
            self.angle[32] = 13.20
            self.angle[33] = 13.61
            self.angle[34] = 14.02
            self.angle[35] = 14.43
            self.angle[36] = 14.85
            self.angle[37] = 15.26
            self.angle[38] = 15.67
            self.angle[39] = 16.08
            self.angle[40] = 16.50
            self.angle[41] = 16.91
            self.angle[42] = 17.32
            self.angle[43] = 17.73
            self.angle[44] = 18.15
            self.angle[45] = 18.56
            self.angle[46] = 18.97
            self.angle[47] = 19.38
            self.angle[48] = 19.79
            self.angle[49] = 20.21
            self.angle[50] = 20.62
            self.angle[51] = 21.03
            self.angle[52] = 21.44
            self.angle[53] = 21.86
            self.angle[54] = 22.27
            self.angle[55] = 22.68
            self.angle[56] = 23.09
            self.angle[57] = 23.51
            self.angle[58] = 23.92
            self.angle[59] = 24.33
            self.angle[60] = 24.74
            self.angle[61] = 25.16
            self.angle[62] = 25.57
            self.angle[63] = 25.98
            self.angle[64] = 26.39
            self.angle[65] = 26.81
            self.angle[66] = 27.22
            self.angle[67] = 27.63
            self.angle[68] = 28.04
            self.angle[69] = 28.46
            self.angle[70] = 28.87
            self.angle[71] = 29.28
            self.angle[72] = 29.69
            self.angle[73] = 30.10
            self.angle[74] = 30.52
            self.angle[75] = 30.93
            self.angle[76] = 31.34
            self.angle[77] = 31.75
            self.angle[78] = 32.17
            self.angle[79] = 32.58
            self.angle[80] = 32.99
            self.angle[81] = 33.40
            self.angle[82] = 33.82
            self.angle[83] = 34.23
            self.angle[84] = 34.64
            self.angle[85] = 35.05
            self.angle[86] = 35.47
            self.angle[87] = 35.88
            self.angle[88] = 36.29
            self.angle[89] = 36.70
            self.angle[90] = 37.12
            self.angle[91] = 37.53
            self.angle[92] = 37.94
            self.angle[93] = 38.35
            self.angle[94] = 38.76
            self.angle[95] = 39.18
            self.angle[96] = 39.59
            self.angle[97] = 40.00
            self.angle[98] = 40.41
            self.angle[99] = 40.83
            self.angle[100] =41.24
            #Real
            self.rp[0]  = 0.014171930042805167
            self.rp[1]  = 0.050581486109776794
            self.rp[2]  = 0.08705729106320187
            self.rp[3]  = 0.12359934490308043
            self.rp[4]  = 0.16020764762941245
            self.rp[5]  = 0.19688219924219794
            self.rp[6]  = 0.2336229997414369
            self.rp[7]  = 0.27043004912712926
            self.rp[8]  = 0.3073033473992752
            self.rp[9]  = 0.3442428945578745
            self.rp[10] = 0.3812486906029273
            self.rp[11] = 0.4183207355344336
            self.rp[12] = 0.45545902935239335
            self.rp[13] = 0.49266357205680655
            self.rp[14] = 0.5299343636476732
            self.rp[15] = 0.5672714041249933
            self.rp[16] = 0.604674693488767
            self.rp[17] = 0.642144231738994
            self.rp[18] = 0.6796800188756746
            self.rp[19] = 0.7172820548988085
            self.rp[20] = 0.7549503398083961
            self.rp[21] = 0.7926848736044371
            self.rp[22] = 0.8304856562869314
            self.rp[23] = 0.8683526878558793
            self.rp[24] = 0.9062859683112805
            self.rp[25] = 0.9442854976531354
            self.rp[26] = 0.9823512758814437
            self.rp[27] = 1.0204833029962053
            self.rp[28] = 1.0586815789974207
            self.rp[29] = 1.0969461038850892
            self.rp[30] = 1.1352768776592113
            self.rp[31] = 1.173673900319787
            self.rp[32] = 1.212137171866816
            self.rp[33] = 1.2506666923002985
            self.rp[34] = 1.2892624616202344
            self.rp[35] = 1.3279244798266239
            self.rp[36] = 1.366652746919467
            self.rp[37] = 1.405447262898763
            self.rp[38] = 1.444308027764513
            self.rp[39] = 1.4832350415167161
            self.rp[40] = 1.522228304155373
            self.rp[41] = 1.5612878156804835
            self.rp[42] = 1.600413576092047
            self.rp[43] = 1.6396055853900644
            self.rp[44] = 1.6788638435745349
            self.rp[45] = 1.718188350645459
            self.rp[46] = 1.7575791066028368
            self.rp[47] = 1.7970361114466675
            self.rp[48] = 1.836559365176952
            self.rp[49] = 1.87614886779369
            self.rp[50] = 1.9158046192968814
            self.rp[51] = 1.9555266196865266
            self.rp[52] = 1.9953148689626248
            self.rp[53] = 2.0351693671251767
            self.rp[54] = 2.0750901141741815
            self.rp[55] = 2.115077110109641
            self.rp[56] = 2.155130354931553
            self.rp[57] = 2.1952498486399183
            self.rp[58] = 2.235435591234738
            self.rp[59] = 2.27568758271601
            self.rp[60] = 2.3160058230837364
            self.rp[61] = 2.356390312337916
            self.rp[62] = 2.396841050478549
            self.rp[63] = 2.4373580375056356
            self.rp[64] = 2.4779412734191752
            self.rp[65] = 2.518590758219169
            self.rp[66] = 2.559306491905616
            self.rp[67] = 2.600088474478516
            self.rp[68] = 2.64093670593787
            self.rp[69] = 2.681851186283677
            self.rp[70] = 2.722831915515938
            self.rp[71] = 2.763878893634652
            self.rp[72] = 2.80499212063982
            self.rp[73] = 2.846171596531441
            self.rp[74] = 2.887417321309515
            self.rp[75] = 2.9287292949740436
            self.rp[76] = 2.9701075175250256
            self.rp[77] = 3.01155198896246
            self.rp[78] = 3.0530627092863485
            self.rp[79] = 3.0946396784966903
            self.rp[80] = 3.1362828965934857
            self.rp[81] = 3.177992363576735
            self.rp[82] = 3.219768079446437
            self.rp[83] = 3.261610044202593
            self.rp[84] = 3.303518257845202
            self.rp[85] = 3.345492720374265
            self.rp[86] = 3.387533431789781
            self.rp[87] = 3.4296403920917506
            self.rp[88] = 3.471813601280174
            self.rp[89] = 3.5140530593550503
            self.rp[90] = 3.5563587663163805
            self.rp[91] = 3.5987307221641642
            self.rp[92] = 3.6411689268984007
            self.rp[93] = 3.6836733805190915
            self.rp[94] = 3.726244083026235
            self.rp[95] = 3.7688810344198327
            self.rp[96] = 3.811584234699884
            self.rp[97] = 3.8543536838663877
            self.rp[98] = 3.897189381919346
            self.rp[99] = 3.9400913288587565
            self.rp[100]= 3.9830595246846214

        if(FOV==4):
            self.angle[0]  = 0.0000000000
            self.angle[1]  = 0.4338504533
            self.angle[2]  = 0.8674744477
            self.angle[3]  = 1.3008860341
            self.angle[4]  = 1.7340992636
            self.angle[5]  = 2.1671281871
            self.angle[6]  = 2.5999868557
            self.angle[7]  = 3.0326893202
            self.angle[8]  = 3.4652496318
            self.angle[9]  = 3.8976818414
            self.angle[10] = 4.3300000000
            self.angle[11] = 4.7622181586
            self.angle[12] = 5.1943503682
            self.angle[13] = 5.6264106798
            self.angle[14] = 6.0584131443
            self.angle[15] = 6.4903718129
            self.angle[16] = 6.9223007364
            self.angle[17] = 7.3542139659
            self.angle[18] = 7.7861255523
            self.angle[19] = 8.2180495467
            self.angle[20] = 8.6500000000
            self.angle[21] = 9.0819869123
            self.angle[22] = 9.5140040795
            self.angle[23] = 9.9460412468
            self.angle[24] = 10.3780881591
            self.angle[25] = 10.8101345614
            self.angle[26] = 11.2421701988
            self.angle[27] = 11.6741848164
            self.angle[28] = 12.1061681591
            self.angle[29] = 12.5381099719
            self.angle[30] = 12.9700000000
            self.angle[31] = 13.4018341923
            self.angle[32] = 13.8336333137
            self.angle[33] = 14.2654243331
            self.angle[34] = 14.6972342194
            self.angle[35] = 15.1290899416
            self.angle[36] = 15.5610184683
            self.angle[37] = 15.9930467687
            self.angle[38] = 16.4252018115
            self.angle[39] = 16.8575105656
            self.angle[40] = 17.2900000000
            self.angle[41] = 17.7226863186
            self.angle[42] = 18.1555426657
            self.angle[43] = 18.5885314207
            self.angle[44] = 19.0216149632
            self.angle[45] = 19.4547556724
            self.angle[46] = 19.8879159278
            self.angle[47] = 20.3210581089
            self.angle[48] = 20.7541445950
            self.angle[49] = 21.1871377656
            self.angle[50] = 21.6200000000
            self.angle[51] = 22.0527105334
            self.angle[52] = 22.4853160236
            self.angle[53] = 22.9178799839
            self.angle[54] = 23.3504659278
            self.angle[55] = 23.7831373688
            self.angle[56] = 24.2159578203
            self.angle[57] = 24.6489907957
            self.angle[58] = 25.0822998085
            self.angle[59] = 25.5159483721
            self.angle[60] = 25.9500000000
            self.angle[61] = 26.3845015478
            self.angle[62] = 26.8194332401
            self.angle[63] = 27.2547586437
            self.angle[64] = 27.6904413255
            self.angle[65] = 28.1264448523
            self.angle[66] = 28.5627327909
            self.angle[67] = 28.9992687081
            self.angle[68] = 29.4360161708
            self.angle[69] = 29.8729387459
            self.angle[70] = 30.3100000000
            self.angle[71] = 30.7471732755
            self.angle[72] = 31.1844710162
            self.angle[73] = 31.6219154414
            self.angle[74] = 32.0595287703
            self.angle[75] = 32.4973332221
            self.angle[76] = 32.9353510162
            self.angle[77] = 33.3736043718
            self.angle[78] = 33.8121155081
            self.angle[79] = 34.2509066444
            self.angle[80] = 34.6900000000
            self.angle[81] = 35.1294153502
            self.angle[82] = 35.5691626951
            self.angle[83] = 36.0092495909
            self.angle[84] = 36.4496835935
            self.angle[85] = 36.8904722593
            self.angle[86] = 37.3316231443
            self.angle[87] = 37.7731438048
            self.angle[88] = 38.2150417968
            self.angle[89] = 38.6573246765
            self.angle[90] = 39.1000000000
            self.angle[91] = 39.5430753235
            self.angle[92] = 39.9865582032
            self.angle[93] = 40.4304561952
            self.angle[94] = 40.8747768557
            self.angle[95] = 41.3195277407
            self.angle[96] = 41.7647164065
            self.angle[97] = 42.2103504091
            self.angle[98] = 42.6564373049
            self.angle[99] = 43.1029846498
            self.angle[100] =43.5500000000
            #Real
            self.rp[0]  = 0.0000000000
            self.rp[1]  = 0.0400000000
            self.rp[2]  = 0.0800000000
            self.rp[3]  = 0.1200000000
            self.rp[4]  = 0.1600000000
            self.rp[5]  = 0.2000000000
            self.rp[6]  = 0.2400000000
            self.rp[7]  = 0.2800000000
            self.rp[8]  = 0.3200000000
            self.rp[9]  = 0.3600000000
            self.rp[10] = 0.4000000000
            self.rp[11] = 0.4400000000
            self.rp[12] = 0.4800000000
            self.rp[13] = 0.5200000000
            self.rp[14] = 0.5600000000
            self.rp[15] = 0.6000000000
            self.rp[16] = 0.6400000000
            self.rp[17] = 0.6800000000
            self.rp[18] = 0.7200000000
            self.rp[19] = 0.7600000000
            self.rp[20] = 0.8000000000
            self.rp[21] = 0.8400000000
            self.rp[22] = 0.8800000000
            self.rp[23] = 0.9200000000
            self.rp[24] = 0.9600000000
            self.rp[25] = 1.0000000000
            self.rp[26] = 1.0400000000
            self.rp[27] = 1.0800000000
            self.rp[28] = 1.1200000000
            self.rp[29] = 1.1600000000
            self.rp[30] = 1.2000000000
            self.rp[31] = 1.2400000000
            self.rp[32] = 1.2800000000
            self.rp[33] = 1.3200000000
            self.rp[34] = 1.3600000000
            self.rp[35] = 1.4000000000
            self.rp[36] = 1.4400000000
            self.rp[37] = 1.4800000000
            self.rp[38] = 1.5200000000
            self.rp[39] = 1.5600000000
            self.rp[40] = 1.6000000000
            self.rp[41] = 1.6400000000
            self.rp[42] = 1.6800000000
            self.rp[43] = 1.7200000000
            self.rp[44] = 1.7600000000
            self.rp[45] = 1.8000000000
            self.rp[46] = 1.8400000000
            self.rp[47] = 1.8800000000
            self.rp[48] = 1.9200000000
            self.rp[49] = 1.9600000000
            self.rp[50] = 2.0000000000
            self.rp[51] = 2.0400000000
            self.rp[52] = 2.0800000000
            self.rp[53] = 2.1200000000
            self.rp[54] = 2.1600000000
            self.rp[55] = 2.2000000000
            self.rp[56] = 2.2400000000
            self.rp[57] = 2.2800000000
            self.rp[58] = 2.3200000000
            self.rp[59] = 2.3600000000
            self.rp[60] = 2.4000000000
            self.rp[61] = 2.4400000000
            self.rp[62] = 2.4800000000
            self.rp[63] = 2.5200000000
            self.rp[64] = 2.5600000000
            self.rp[65] = 2.6000000000
            self.rp[66] = 2.6400000000
            self.rp[67] = 2.6800000000
            self.rp[68] = 2.7200000000
            self.rp[69] = 2.7600000000
            self.rp[70] = 2.8000000000
            self.rp[71] = 2.8400000000
            self.rp[72] = 2.8800000000
            self.rp[73] = 2.9200000000
            self.rp[74] = 2.9600000000
            self.rp[75] = 3.0000000000
            self.rp[76] = 3.0400000000
            self.rp[77] = 3.0800000000
            self.rp[78] = 3.1200000000
            self.rp[79] = 3.1600000000
            self.rp[80] = 3.2000000000
            self.rp[81] = 3.2400000000
            self.rp[82] = 3.2800000000
            self.rp[83] = 3.3200000000
            self.rp[84] = 3.3600000000
            self.rp[85] = 3.4000000000
            self.rp[86] = 3.4400000000
            self.rp[87] = 3.4800000000
            self.rp[88] = 3.5200000000
            self.rp[89] = 3.5600000000
            self.rp[90] = 3.6000000000
            self.rp[91] = 3.6400000000
            self.rp[92] = 3.6800000000
            self.rp[93] = 3.7200000000
            self.rp[94] = 3.7600000000
            self.rp[95] = 3.8000000000
            self.rp[96] = 3.8400000000
            self.rp[97] = 3.8800000000
            self.rp[98] = 3.9200000000
            self.rp[99] = 3.9600000000
            self.rp[100]= 4.0000000000
        
        # self.x_rp = np.arange(self.rp.size)
        # coefficients  = np.polyfit(self.x_rp, self.rp, 2)
        # poly = np.poly1d(coefficients)
        # self.rp = poly(self.x_rp)
        
        self.lensTableSize=100
        self.sensorPointSizeMM=0.02

        r0=1-height/2+offsetX #-119
        c0=1-width/2+offsetY  #-159


        row=r0
        col=c0
        for y in range (height):
            col=c0
            for x in range (width):

                c=col-0.5 #from -159.5 to 159.5
                r=row-0.5 #from -119.5 to 119.5

                angleGrad= self.getAngle(c,r, self.sensorPointSizeMM)
                angleRad =angleGrad*np.pi / 180.0

                rp=rp = math.sqrt(c * c + r * r)
                rUA=math.sin(angleRad)


                self.xUA[x][y] = c * rUA / rp
                self.yUA[x][y] = r * rUA / rp
                self.zUA[x][y] = math.cos(angleRad)


                col=col+1
            row=row+1

    def getAngle(self,x,y,sensorPointSizeMM):

        radius=sensorPointSizeMM*math.sqrt(x*x+y*y)


        alphaGrad=0
        for i in range (self.lensTableSize):
            if(radius>=self.rp[i-1] and radius<=self.rp[i]):
                alphaGrad=self.interpolate(radius, self.rp[i-1], self.angle[i-1], self.rp[i], self.angle[i])
        return alphaGrad

    def interpolate(self, x_in, x0,y0,x1,y1):
        if((x1-x0)<0.001):
            return y0
        else:
            return ((x_in-x0)*(y1-y0)/(x1-x0) + y0)

    def transformPixel(self,srcX,srcY,srcZ):

        destX = srcZ * self.xUA[srcX][srcY]
        destY = srcZ * self.yUA[srcX][srcY]
        destZ = srcZ * self.zUA[srcX][srcY]

        return ((destX,destY,destZ))

    def transformX(self,srcX,srcY,srcZ):
        destX = srcZ * self.xUA[srcX][srcY]
        return destX

    def transformY(self,srcX,srcY,srcZ):
        destY = srcZ * self.yUA[srcX][srcY]
        return destY

    def transformZ(self,srcX,srcY,srcZ):
        destZ = srcZ * self.zUA[srcX][srcY]
        return destZ

    def transformImage(self,srcI,startX,endX,startY,endY):

        srcI[:,:,1]=np.multiply(srcI[:,:,0],self.xUA[startX:(endX+1),startY:(endY+1)])
        srcI[:,:,2]=np.multiply(srcI[:,:,0],self.yUA[startX:(endX+1),startY:(endY+1)])
        srcI[:,:,3]=np.multiply(srcI[:,:,0],self.zUA[startX:(endX+1),startY:(endY+1)])


    def undistort(img,param="parameters.npz"):
        # basic setting and parameters acquisition
        parameters = np.load(param)
        mtx = parameters["mtx"]
        dist = parameters["dist"]

        print(mtx)
        print(dist)

        h,  w = img.shape[:2]
        newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))
        #undistort
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        ##crop the image
        x,y,w,h = roi
        dst = dst[y:y+h, x:x+w]
        return dst

    def depth_to_3d(depth, camera_matrix):
        # Get the shape of the depth image
        height, width = depth.shape

        # Create a grid of indices
        x, y = np.indices((height, width))

        # Normalize the x and y coordinates by the optical center
        x = (x - camera_matrix[0, 2]) / camera_matrix[0, 0]
        y = (y - camera_matrix[1, 2]) / camera_matrix[1, 1]

        # Stack the coordinates into a (3, N) array
        coords = np.stack((x, y, np.ones_like(x)), axis=0).reshape(3, -1)

        # Multiply the coordinates by the depth to get 3D points
        points = coords * depth.reshape(1, -1)

        return points
    
    def remove_center_pixel(self, b):
        if b[0]==0 and b[1]==0:
            return [0,0,0]
        else:
            return b
    
    def depth_to_3d_1(self, depth):
        frame_dist_depth_image = depth
        frame_dist_xyz= np.zeros((320,240,4))
        frame_dist_xyz[:,:,0] = np.transpose(np.fliplr(frame_dist_depth_image))

        self.transformImage(frame_dist_xyz,0,319,0,239)

        xyz_image = frame_dist_xyz[:,:,1:].reshape(240*320,3,order='F')
        xyz_image = np.delete(xyz_image, np.where(xyz_image > 10000), axis=0)
        xyz_image = np.apply_along_axis(self.remove_center_pixel, -1, xyz_image)
        xyz_image = np.delete(xyz_image, np.where(xyz_image[:,2]==0), axis=0)

        return xyz_image.T