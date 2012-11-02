MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = downmodis rmodislib convertmodis parsemodis

DSTDIR = $(ETC)

PYFILES := $(patsubst %,$(DSTDIR)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(DSTDIR)/%.pyc,$(MODULES))

default: $(PYFILES) $(PYCFILES)

$(DSTDIR):
	$(MKDIR) $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@

install:
	cp -r $(DSTDIR) $(INST_DIR)/etc/
