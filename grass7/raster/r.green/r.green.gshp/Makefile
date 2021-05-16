MODULE_TOPDIR = ../../..

PGM = r.green.gshp

SUBDIRS = libgshp \
	r.green.gshp.theoretical \
	r.green.gshp.technical

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
