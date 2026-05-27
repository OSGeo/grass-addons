MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

PGM = r.richdem
LIBDIR = librichdem
ETCDIR = $(ETC)/$(PGM)/$(LIBDIR)

MODULES = __init__ raster vector

PYFILES  := $(patsubst %,$(ETCDIR)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(ETCDIR)/%.pyc,$(MODULES))

default: $(PYFILES) $(PYCFILES)

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

install:
	$(MKDIR) $(INST_DIR)/etc/$(PGM)
	cp -r $(ETCDIR) $(INST_DIR)/etc/$(PGM)/$(LIBDIR)
