MODULE_TOPDIR = ../..

PGM = i.segment.hierarchical

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = isegpatch

ETCDIR = $(ETC)/$(PGM)

ETCFILES := $(patsubst %,$(ETCDIR)/%.py,$(MODULES))

default: $(ETCFILES) script

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@
