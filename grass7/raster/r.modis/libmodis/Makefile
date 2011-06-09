MODULE_TOPDIR = ../../..

PGM = libmodis

include $(MODULE_TOPDIR)/include/Make/Script.make

SRCFILES = rmodislib.py modis.py
DSTFILES := $(patsubst %,$(ETC)/r.modis/%,$(SRCFILES))

default: $(DSTFILES)

$(ETC)/r.modis/%: % | $(ETC)/r.modis
	$(INSTALL) $< $@

$(ETC)/r.modis:
	$(MKDIR) $@
