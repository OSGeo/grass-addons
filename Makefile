MODULE_TOPDIR = ..

SUBDIRS = \
	database \
	display \
	general \
	gui \
	HydroFOSS \
	imagery \
	IPCC \
	LandDyn \
	misc \
	ossim_grass \
	postscript \
	raster \
	vector

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: htmldir

htmldir: subdirs

clean: cleansubdirs
