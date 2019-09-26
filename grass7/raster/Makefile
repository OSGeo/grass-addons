MODULE_TOPDIR = ..

# Further possibly deprecated modules
#	r.le.patch \
#	r.le.pixel \
#	r.le.setup \
#	r.le.trace

ALL_SUBDIRS := ${sort ${dir ${wildcard */.}}}
DEPRECATED_SUBDIRS := ${sort ${dir ${wildcard */DEPRECATED}}}
SUBDIRS := $(filter-out $(DEPRECATED_SUBDIRS), $(ALL_SUBDIRS))

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: subdirs
