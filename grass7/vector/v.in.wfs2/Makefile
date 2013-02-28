MODULE_TOPDIR = ../..

PGM = v.in.wfs2

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = wfs_base wfs_drv wfs_owslib_drv
PYFILES := $(patsubst %,$(ETC)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(ETC)/%.pyc,$(MODULES))

default: script $(PYFILES) $(PYCFILES)

$(ETCDIR):
	$(MKDIR) $@

$(ETC)/%: % | $(ETC)
	$(INSTALL_DATA) $< $@
