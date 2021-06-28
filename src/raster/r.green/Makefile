MODULE_TOPDIR = ../..

PGM = r.green

SUBDIRS = libgreen \
	r.green.biomassfor \
	r.green.hydro \
	r.green.gshp \
	r.green.install

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
