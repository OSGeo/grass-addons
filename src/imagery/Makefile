MODULE_TOPDIR = ..

# Deprecated
#	i.fusion.brovey
#	i.pr_statistics (relies on D_* and R_* functions)
#	i.pr_training (relies on the site library)

ALL_SUBDIRS := ${sort ${dir ${wildcard */.}}}
DEPRECATED_SUBDIRS := ${sort ${dir ${wildcard */DEPRECATED}}}
SUBDIRS := $(filter-out $(DEPRECATED_SUBDIRS), $(ALL_SUBDIRS))

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: subdirs
