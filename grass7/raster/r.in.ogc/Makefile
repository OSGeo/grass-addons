MODULE_TOPDIR = ../..

PGM = r.in.ogc

SUBDIRS = r.in.ogc.coverages

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
