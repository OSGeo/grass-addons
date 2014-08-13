MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(INST_DIR)/etc/metadata

MODULES = $(wildcard *.py)

PYFILES := $(patsubst %,$(DSTDIR)/%,$(MODULES))
PYCFILES := $(patsubst %.py,$(DSTDIR)/%.pyc,$(filter %.py,$(MODULES)))

default:

install: $(PYFILES) $(PYCFILES)

$(DSTDIR):
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
