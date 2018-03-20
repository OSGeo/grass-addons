MODULE_TOPDIR =../..

PGM = i.modis

SUBDIRS = libmodis \
        i.modis.download \
        i.modis.import \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
