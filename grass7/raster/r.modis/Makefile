MODULE_TOPDIR =../..

PGM = r.modis

SUBDIRS = libmodis \
        r.modis.download \
        r.modis.import \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
