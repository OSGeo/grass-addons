MODULE_TOPDIR = ..

SUBDIRS = \
	g.extension \
	g.region.point
## already in 6.4+:
#	g.xlist \
#	g.xremove \
## external program:
#	grass_create_location

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: htmldir

htmldir: subdirs

clean: cleansubdirs
