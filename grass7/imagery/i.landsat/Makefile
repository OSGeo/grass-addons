MODULE_TOPDIR =../..

PGM = i.landsat

SUBDIRS = i.landsat.download \
        i.landsat.import \
        i.landsat.qa \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
