MODULE_TOPDIR =../..

PGM = i.sar

SUBDIRS = i.sar.amplitude \
        i.sar.pauliRGB \
        i.sar.speckle \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
