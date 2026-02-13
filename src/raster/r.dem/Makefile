MODULE_TOPDIR =../..

PGM = r.dem

SUBDIRS = libstac \
        r.dem.nk \
        t.dem.icp \

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
