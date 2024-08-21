MODULE_TOPDIR =../..

PGM = t.stac

SUBDIRS = libstac \
        t.stac.catalog \
        t.stac.collection \
        t.stac.item \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
