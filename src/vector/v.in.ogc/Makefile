MODULE_TOPDIR = ../..

PGM = v.in.ogc

SUBDIRS = v.in.ogc.features

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
