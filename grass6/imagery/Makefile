MODULE_TOPDIR = ..

SUBDIRS = \
	i.homography \
	i.landsat.dehaze \
	i.points.auto \
	i.pr \
	i.spec.sam \
	i.spec.unmix \
	i.warp

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: htmldir

htmldir: subdirs

clean: cleansubdirs
