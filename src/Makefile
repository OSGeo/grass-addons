MODULE_TOPDIR = ..

SUBDIRS = \
	dst \
	database \
	display \
	general \
	gui \
	HydroFOSS \
	imagery \
	misc \
	ossim_grass \
	postscript \
	raster \
	raster3d \
	vector

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: htmldir

htmldir: subdirs

clean: cleansubdirs
