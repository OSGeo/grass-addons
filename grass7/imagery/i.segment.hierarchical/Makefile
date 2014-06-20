MODULE_TOPDIR = ../..

PGM = i.segment.hierarchical

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = isegpatch

ETCDIR = $(ETC)/i.segment.hierarchical

PYFILES := $(patsubst %,$(ETCDIR)/%.py,$(MODULES))

default: script $(PYFILES)

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@
