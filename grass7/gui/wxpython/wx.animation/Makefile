MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Dir.make
include $(MODULE_TOPDIR)/include/Make/Python.make

ETCDIR = $(ETC)/gui/wxpython
ICONDIR = $(ETC)/gui

SRCFILES := $(wildcard animation/*)
DSTFILES := $(patsubst %,$(ETCDIR)/%,$(SRCFILES)) $(patsubst %.py,$(ETCDIR)/%.pyc,$(filter %.py,$(SRCFILES)))
HTMLFILES := $(wildcard *.html)
ICONFILES := $(wildcard icons/grass/*.png)

DSTDIRS := $(patsubst %,$(ETCDIR)/%,animation)

default: $(DSTFILES) $(patsubst %,$(HTMLDIR)/%,$(HTMLFILES)) $(patsubst %,$(ICONDIR)/%,$(ICONFILES))
	$(MAKE) parsubdirs

$(ETCDIR)/%: % | $(DSTDIRS)
	$(INSTALL_DATA) $< $@

$(ICONDIR)/%: % | $(DSTDIRS)
	$(INSTALL_DATA) $< $@

$(DSTDIRS): %: | $(ETCDIR)
	$(MKDIR) $@

$(ETCDIR):
	$(MKDIR) $@
