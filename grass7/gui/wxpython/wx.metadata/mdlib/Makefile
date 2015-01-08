MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(ETC)/mdlib

MODULES = $(wildcard *.py)

PYFILES := $(patsubst %,$(DSTDIR)/%,$(MODULES))
PYCFILES := $(patsubst %.py,$(DSTDIR)/%.pyc,$(filter %.py,$(MODULES)))

default: $(PYFILES) $(PYCFILES)

install:
	@cp -rL $(DSTDIR) $(INST_DIR)

$(DSTDIR):
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
