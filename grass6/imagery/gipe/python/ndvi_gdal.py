#!/bin/python

#---------------------------------------------
# Inspired from Howard Butler and Sean Gillies 
# During the OSGEO'05
# Yann Chemin, LGPL, 2006
#------------------------

import os.path
#equivalent to pwd
#os.path.abspath('./hobu.txt')

import glob
# Make a tuple of hdf files available in directory
#glob.glob('*.hdf')

paths = glob.glob('*.hdf')
	for path in paths:
		ds = gdal.Open(path)
		geo = ds.GetGeoTransform()
		pixels = ds.RasterXSize
		lines = ds.RasterYSize
		minx = geo[0]
		maxx = minx + pixels * geo[1]
		maxy = geo[3]
		miny = maxy + lines * geo[5]
		print os.path.basename(path), (minx, miny, maxx, maxy)
		del ds