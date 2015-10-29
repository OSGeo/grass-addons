MODULE_TOPDIR =../..

PGM = r.modis

SUBDIRS = \
        r.modis.download \
        r.modis.import \
	libmodis

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
