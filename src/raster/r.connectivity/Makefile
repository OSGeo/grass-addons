MODULE_TOPDIR = ../..

PGM = r.connectivity

SUBDIRS = r.connectivity.distance  \
	r.connectivity.network  \
	r.connectivity.corridors

###  libconnectivity \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
