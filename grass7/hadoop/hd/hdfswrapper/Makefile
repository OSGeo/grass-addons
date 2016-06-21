MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(ETC)/hd/hdfswrapper

MODULES = $(wildcard *.py)

PYFILES := $(patsubst %,$(DSTDIR)/%,$(MODULES))
PYCFILES := $(patsubst %.py,$(DSTDIR)/%.pyc,$(filter %.py,$(MODULES)))

default: $(PYFILES) $(PYCFILES)

install:
	$(MKDIR) $(INST_DIR)/etc/hd/hdfswrapper
	@cp -rL $(DSTDIR) $(INST_DIR)/etc/hd

$(DSTDIR):
	$(MKDIR) -p $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
