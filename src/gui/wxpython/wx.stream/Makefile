MODULE_TOPDIR = ../..

#SUBDIRS = docs images

include $(MODULE_TOPDIR)/include/Make/Dir.make
include $(MODULE_TOPDIR)/include/Make/Python.make

ifeq ($(GRASS_VERSION_MAJOR), 7)
ETCDIR = $(ETC)/gui/wxpython
else
ETCDIR = $(ETC)/wxpython
endif

#SRCFILES := $(wildcard gui_modules/* xml/*)
SRCFILES := $(wildcard gui_modules/*)
DSTFILES := $(patsubst %,$(ETCDIR)/%,$(SRCFILES)) $(patsubst %.py,$(ETCDIR)/%.pyc,$(filter %.py,$(SRCFILES)))

#DSTDIRS := $(patsubst %,$(ETCDIR)/%,gui_modules xml)
DSTDIRS := $(patsubst %,$(ETCDIR)/%,gui_modules)

default: $(DSTFILES)
	$(MAKE) parsubdirs

$(ETCDIR)/%: % | $(DSTDIRS)
	$(INSTALL_DATA) $< $@

$(DSTDIRS): %: | $(ETCDIR)
	$(MKDIR) $@

$(ETCDIR):
	$(MKDIR) $@
