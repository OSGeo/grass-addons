MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make



SUBDIRS = \
	r.boxcount \
	r.boxcount.sh \
	v.strahler

default: subdirs

clean: cleansubdirs
