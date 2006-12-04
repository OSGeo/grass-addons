MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make



SUBDIRS = \
	v.strahler

default: subdirs

clean: cleansubdirs
