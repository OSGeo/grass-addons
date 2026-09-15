MODULE_TOPDIR =../..

PGM = r.dem

SUBDIRS = r.dem.nk \
        r.dem.icp \
        r.dem.bias \
        r.dem.stats \
        r.dem.errprop \
        r.dem.change \
        r.dem.lod \
        r.dem.coregister \
        r.dem.screen

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
	$(INSTALL_DATA) r_dem_workflow.png $(INST_DIR)/docs/html/
