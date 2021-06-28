MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = agent anthill ant error grassland playground world __init__

PGM = r.agent
LIBDIR = libagent
ETCDIR = $(ETC)/$(PGM)/$(LIBDIR)

PYFILES := $(patsubst %,$(ETCDIR)/%.py,$(MODULES))
PYCFILES := $(patsubst %,$(ETCDIR)/%.pyc,$(MODULES))

default: $(PYFILES) $(PYCFILES)

$(ETCDIR):
	$(MKDIR) $@

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

install:
	$(MKDIR) $(INST_DIR)/etc/$(PGM)
	cp -r $(ETCDIR) $(INST_DIR)/etc/$(PGM)/$(LIBDIR)
