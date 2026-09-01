MODULE_TOPDIR =../..

PGM = i.saocom

SUBDIRS = i.saocom.geocode \
        i.saocom.import \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
