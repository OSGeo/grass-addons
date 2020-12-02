#!/usr/bin/env
import numpy as np

#Spectral data to load as maps
# Band: r g b i1 i2 i3
# Spektren zeilenweise eingeben!
# 1. Sagebrush
# 2. Saltbush
# 3. Ground
# 4. Dry Grass
#row0:  8.87  13.14  11.71  35.85
#Matrix: 4 by 4
#row0:  8.87  13.14  11.71  35.85
#row1: 13.59  20.12  19.61  50.66
#row2: 28.26  34.82  38.27  40.1
#row3: 10.54  16.35  23.7   38.98

#Define the spectral signatures for each land use class
cls1 = [8.87, 13.14, 11.71, 35.85]
cls2 = [13.59, 20.12, 19.61, 50.66]
cls3 = [28.26, 34.82, 38.27, 40.10]
cls4 = [10.54, 16.35, 23.70, 38.98]

#Generate a disturbed class manually
cls1_wannabe = [9, 14, 12, 36]
cls2_wannabe = [14, 21, 20, 51]
cls3_wannabe = [29, 35, 39, 41]
cls4_wannabe = [11, 17, 24, 39]


#Define Norm of a Vector product
def prod(v1, v2):
	return np.sum(np.multiply(v1,v2))

#Define Euclidian Norm of a vector ("L2-norm")
def l2(v):
	return np.sqrt((np.multiply(v,v)).sum(axis=0))


#Define Spectral Angle (degrees) of a vector pair
def specangle(v1,v2):
	return np.arccos(prod(v1,v2)/(l2(v1)*l2(v2)))*180/np.pi


#Run for all 4 classes
print("cls1")
print(cls1)
print(cls1_wannabe)
print(prod(cls1,cls1_wannabe))
print (specangle(cls1,cls1_wannabe))

print("cls2")
print(cls2)
print(cls2_wannabe)
print(prod(cls2,cls2_wannabe))
print (specangle(cls2,cls2_wannabe))

print("cls3")
print(cls3)
print(cls3_wannabe)
print(prod(cls3,cls3_wannabe))
print (specangle(cls3,cls3_wannabe))

print("cls4")
print(cls4)
print(cls4_wannabe)
print(prod(cls4,cls4_wannabe))
print (specangle(cls4,cls4_wannabe))


"""
python test1_spec_angle.py
cls1
[8.87, 13.14, 11.71, 35.85]
[9, 14, 12, 36]
1.06564745443
cls2
[13.59, 20.12, 19.61, 50.66]
[14, 21, 20, 51]
0.707938132625
cls3
[28.26, 34.82, 38.27, 40.1]
[29, 35, 39, 41]
0.422563007246
cls4
[10.54, 16.35, 23.7, 38.98]
[11, 17, 24, 39]
0.811223847592

"""
