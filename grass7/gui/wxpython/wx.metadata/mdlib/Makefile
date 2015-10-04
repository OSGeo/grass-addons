MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

DSTDIR = $(ETC)/wx.metadata/mdlib

MODULES = $(wildcard *.py)

PYFILES := $(patsubst %,$(DSTDIR)/%,$(MODULES))
PYCFILES := $(patsubst %.py,$(DSTDIR)/%.pyc,$(filter %.py,$(MODULES)))

default: $(PYFILES) $(PYCFILES)

install:
	$(MKDIR) $(INST_DIR)/etc/wx.metadata/mdlib
	@cp -rL $(DSTDIR) $(INST_DIR)/etc/wx.metadata/mdlib

$(DSTDIR):
	$(MKDIR) -p $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
