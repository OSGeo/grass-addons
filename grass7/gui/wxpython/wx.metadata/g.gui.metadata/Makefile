MODULE_TOPDIR = ../..

PGM = g.gui.metadata

include $(MODULE_TOPDIR)/include/Make/GuiScript.make
include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(ETC)

MODULES = editor.py

PYFILES := $(patsubst %,$(DSTDIR)/%,$(MODULES))
PYCFILES := $(patsubst %.py,$(DSTDIR)/%.pyc,$(filter %.py,$(MODULES)))

default: $(PYFILES) $(PYCFILES) guiscript

$(DSTDIR):
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
