MODULE_TOPDIR = ../..

PGM=r.green

SUBDIRS = r.green.hydro/libhydro \
	r.green.biomassfor \
	r.green.hydro \
	r.green.install \
	libgreen

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
