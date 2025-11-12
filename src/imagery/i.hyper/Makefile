MODULE_TOPDIR = ../..

SUBDIRS = i_hyper_lib \
        i.hyper.import \
        i.hyper.preproc \
        i.hyper.explore \
        i.hyper.export \
        i.hyper.composite

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

install: installsubdirs
	$(INSTALL_DATA) i.hyper.html $(INST_DIR)/docs/html/
