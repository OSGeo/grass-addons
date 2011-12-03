MODULE_TOPDIR = ..

SUBDIRS = \
	i.homography \
	i.landsat.acca \
	i.landsat.dehaze \
	i.landsat.toar \
	i.points.auto \
	i.points.reproj \
	i.pr \
	i.spec.grass63 \
	i.spec.sam \
	i.spec.unmix \
	i.topo.corr \
	i.warp

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: htmldir

htmldir: subdirs

clean: cleansubdirs
