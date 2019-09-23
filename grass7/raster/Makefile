MODULE_TOPDIR = ..

# commands replaced with more modern commands in trunk/relbranch
OLD = \
	r.in.arc \
	r.out.arc \
	r.out.tiff \
#	r.le.patch \
#	r.le.pixel \
#	r.le.setup \
#	r.le.trace

ALL_SUBDIRS := ${sort ${dir ${wildcard */.}}}
DEPRECATED_SUBDIRS := ${sort ${dir ${wildcard */DEPRECATED}}}
SUBDIRS := $(filter-out $(DEPRECATED_SUBDIRS), $(ALL_SUBDIRS))

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: subdirs
