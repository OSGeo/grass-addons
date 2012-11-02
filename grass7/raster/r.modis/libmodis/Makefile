MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = downmodis rmodislib convertmodis parsemodis

PYFILES := $(patsubst %,$(ETC)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(ETC)/%.pyc,$(MODULES))

default: $(PYFILES) $(PYCFILES)

$(DSTDIR):
	$(MKDIR) $@

$(ETC)/%: % | $(ETC)
	$(INSTALL_DATA) $< $@

install:
	cp -r $(ETC) $(INST_DIR)
