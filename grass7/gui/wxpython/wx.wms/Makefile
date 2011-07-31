MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Python.make

ETCDIR = $(ETC)/gui/wxpython/gui_modules/wms

SRCFILES := $(wildcard *.py)
DSTFILES := $(patsubst %,$(ETCDIR)/%,$(SRCFILES)) $(patsubst %.py,$(ETCDIR)/%.pyc,$(filter %.py,$(SRCFILES)))

default: $(DSTFILES)

$(ETCDIR):
	$(MKDIR) $@
