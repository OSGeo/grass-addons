MODULE_TOPDIR = ../..

PGM = r.sentinel

SUBDIRS = \
	r.sentinel.download \
        r.sentinel.import

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
