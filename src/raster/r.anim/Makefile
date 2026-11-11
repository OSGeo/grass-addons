MODULE_TOPDIR =../..

PGM = r.anim

SUBDIRS = r.anim.morph

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
