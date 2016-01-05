#!/usr/bin/env python

#This creates 4 spectral maps
#Each map has 4 horizontal sections
#Each horizontal section is a test spectral class  

# -*- coding: utf-8 -*-
from __future__ import (nested_scopes, generators, division, absolute_import,
                        with_statement, print_function, unicode_literals)

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
cls1=[8.87, 13.14, 11.71, 35.85]
cls2=[13.59, 20.12, 19.61, 50.66]
cls3=[28.26, 34.82, 38.27, 40.10]
cls4=[10.54, 16.35, 23.70, 38.98]

#Generate a disturbed class manually 
cls1_wannabe=[9, 14, 12, 36]
cls2_wannabe=[14, 21, 20, 51]
cls3_wannabe=[29, 35, 39, 41]
cls4_wannabe=[11, 17, 24, 39]

# Load Library
from grass.pygrass.raster import RasterSegment
from grass.pygrass.gis.region import Region

#Raster layers names
outrast1='sam_test_b1'
outrast2='sam_test_b2'
outrast3='sam_test_b3'
outrast4='sam_test_b4'

# Create output raster file
out1 = RasterSegment(outrast1)
out2 = RasterSegment(outrast2)
out3 = RasterSegment(outrast3)
out4 = RasterSegment(outrast4)

# we must specify the map type the default is "CELL"
out1.open('w', mtype='DCELL', overwrite=True)
out2.open('w', mtype='DCELL', overwrite=True)
out3.open('w', mtype='DCELL', overwrite=True)
out4.open('w', mtype='DCELL', overwrite=True)
	
# Get the number of rows
rg = Region()

# Loop through the rows
for r in range(rg.rows):
    '''Loop through the region rows'''
    if(r < (1/4.0 * rg.rows)):
        for c in range(rg.cols):
            out1.put(r,c,cls1_wannabe[0])
            out2.put(r,c,cls1_wannabe[1])
            out3.put(r,c,cls1_wannabe[2])
            out4.put(r,c,cls1_wannabe[3])
    elif(r >= (1/4.0 * rg.rows) and r < (1/2.0 * rg.rows)):
        for c in range(rg.cols):
            out1.put(r,c,cls2_wannabe[0])
            out2.put(r,c,cls2_wannabe[1])
            out3.put(r,c,cls2_wannabe[2])
            out4.put(r,c,cls2_wannabe[3])
    elif(r >= (1/2.0 * rg.rows) and r < (3/4.0 * rg.rows)):
        for c in range(rg.cols):
            out1.put(r,c,cls3_wannabe[0])
            out2.put(r,c,cls3_wannabe[1])
            out3.put(r,c,cls3_wannabe[2])
            out4.put(r,c,cls3_wannabe[3])
    else:
        for c in range(rg.cols):
            out1.put(r,c,cls4_wannabe[0])
            out2.put(r,c,cls4_wannabe[1])
            out3.put(r,c,cls4_wannabe[2])
            out4.put(r,c,cls4_wannabe[3])
	
# Close the raster maps
out1.close()
out2.close()
out3.close()
out4.close()
