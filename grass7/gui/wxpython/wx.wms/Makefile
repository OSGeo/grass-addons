MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Other.make
include $(MODULE_TOPDIR)/include/Make/Python.make

ETCDIR = $(ETC)/gui/wxpython/gui_modules/wms

SRCFILES := $(wildcard *.py) ServersList.xml
DSTFILES := $(patsubst %,$(ETCDIR)/%,$(SRCFILES)) $(patsubst %.py,$(ETCDIR)/%.pyc,$(filter %.py,$(SRCFILES)))

default: $(DSTFILES)

$(ETCDIR)/%: % | $(ETCDIR)
	$(INSTALL_DATA) $< $@

$(ETCDIR):
	$(MKDIR) $@
