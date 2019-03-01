MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

MODULES = __init__ accessibility colors components constants distance grassy_utilities labels main mobility normalisation panos spectrum supply_and_use utilities

PGM = r.estimap.recreation
LIBDIR = estimap_recreation
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
