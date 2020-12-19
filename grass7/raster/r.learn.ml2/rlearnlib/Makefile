  MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = stats utils indexing raster transformers

ETCDIR = $(ETC)/r.learn.ml2/rlearnlib

PYFILES := $(patsubst %,$(ETCDIR)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(ETCDIR)/%.pyc,$(MODULES))

default: $(PYFILES) $(PYCFILES)

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

install:
	$(MKDIR) $(INST_DIR)/etc/r.learn.ml2/rlearnlib
	cp -r $(ETCDIR) $(INST_DIR)/etc/r.learn.ml2
