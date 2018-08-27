MODULE_TOPDIR = ../..

PGM = i.sentinel

SUBDIRS = \
	i.sentinel.download \
        i.sentinel.import \
	i.sentinel.preproc \
	i.sentinel.mask

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
