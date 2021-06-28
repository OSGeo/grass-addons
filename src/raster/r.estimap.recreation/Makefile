MODULE_TOPDIR = ../..

PGM = r.estimap.recreation

SUBDIRS = estimap_recreation \
          r.estimap.recreation

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM)/$(PGM).html $(INST_DIR)/docs/html/
