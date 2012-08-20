MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Dir.make
include $(MODULE_TOPDIR)/include/Make/Python.make

ETCDIR = $(ETC)/gui/wxpython

SRCFILES := $(wildcard vnet/*)
DSTFILES := $(patsubst %,$(ETCDIR)/%,$(SRCFILES)) $(patsubst %.py,$(ETCDIR)/%.pyc,$(filter %.py,$(SRCFILES)))
HTMLFILES := $(wildcard *.html)

DSTDIRS := $(patsubst %,$(ETCDIR)/%,vnet)

default: $(DSTFILES) $(patsubst %,$(HTMLDIR)/%,$(HTMLFILES))
	$(MAKE) parsubdirs

$(ETCDIR)/%: % | $(DSTDIRS)
	$(INSTALL_DATA) $< $@

$(DSTDIRS): %: | $(ETCDIR)
	$(MKDIR) $@

$(ETCDIR):
	$(MKDIR) $@
