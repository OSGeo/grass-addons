MODULE_TOPDIR = ../..

PGM = r.learn.ml2

SUBDIRS = rlearnlib \
	  r.learn.train \
	  r.learn.predict \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
