MODULE_TOPDIR = ../..

PGM = i.sentinel

ALL_SUBDIRS := ${sort ${dir ${wildcard */.}}}
DEPRECATED_SUBDIRS := ${sort ${dir ${wildcard */DEPRECATED}}}
SUBDIRS := $(filter-out $(DEPRECATED_SUBDIRS), $(ALL_SUBDIRS))

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: subdirs htmldir

install:
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
