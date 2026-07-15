MODULE_TOPDIR = ../..

PGM = i.hyper

SUBDIRS = libsixsv i.hyper.atcorr i.hyper.composite i.hyper.explore \
          i.hyper.export i.hyper.import i.hyper.metadata i.hyper.preproc \
          i.hyper.specresamp i_hyper_lib

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: subdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
