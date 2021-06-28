MODULE_TOPDIR =../../..

PGM = i.ann.maskrcnn

SUBDIRS = maskrcnnlib \
	i.ann.maskrcnn.train \
	i.ann.maskrcnn.detect \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
