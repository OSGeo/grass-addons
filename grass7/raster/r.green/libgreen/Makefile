MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = utils checkparameter


LIBGREENDIR = $(ETC)/r.green
ETCDIR = $(LIBGREENDIR)/libgreen


PYFILES := $(patsubst %,$(ETCDIR)/%.py,$(MODULES) __init__)
PYCFILES := $(patsubst %,$(ETCDIR)/%.pyc,$(MODULES) __init__)

default: $(PYFILES) $(PYCFILES) $(ETCDIR)/__init__.py $(ETCDIR)/__init__.pyc

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

install:
	cp -r $(ETCDIR) $(INST_DIR)
