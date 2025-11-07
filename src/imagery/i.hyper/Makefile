MODULE_TOPDIR = ../..

PGM = i.hyper

SUBDIRS = i_hyper_lib \
        i.hyper.import \
        i.hyper.preproc \
        i.hyper.explore \
        i.hyper.export \
        i.hyper.composite

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
