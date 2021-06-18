MODULE_TOPDIR = ../..

PGM = r.in.wms2.py

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = wms_base wms_drv wms_gdal_drv wms_cap_parsers
ETCDIR = $(ETC)/r.in.wms2
PYFILES := $(patsubst %,$(ETCDIR)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(ETCDIR)/%.pyc,$(MODULES))

default: script $(PYFILES) $(PYCFILES)

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@
