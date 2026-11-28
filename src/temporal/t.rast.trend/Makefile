MODULE_TOPDIR = ../..

PGM = t.rast.trend

SUBDIRS = trendlib \
	  t.rast.stl \
	  t.rast.stl2ca \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
