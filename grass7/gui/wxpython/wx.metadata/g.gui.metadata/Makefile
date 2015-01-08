MODULE_TOPDIR = ../..

PGM = g.gui.metadata

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(ETC)/mdlib

MODULES = editor.py

PYFILES := $(patsubst %,$(DSTDIR)/%,$(MODULES))
PYCFILES := $(patsubst %.py,$(DSTDIR)/%.pyc,$(filter %.py,$(MODULES)))

default: $(PYFILES) $(PYCFILES) script

$(DSTDIR):
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
