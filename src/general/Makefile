MODULE_TOPDIR = ..

SUBDIRS = \
	g.md5sum \
	g.name.sequence \
	g.region.grow \
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
