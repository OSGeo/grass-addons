MODULE_TOPDIR = ..

SUBDIRS = \
	database \
	display \
	general \
	gui \
	HydroFOSS \
	imagery \
	IPCC \
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
