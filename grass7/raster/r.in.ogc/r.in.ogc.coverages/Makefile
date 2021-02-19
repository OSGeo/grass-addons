MODULE_TOPDIR = ../../..

PGM = r.in.ogc.coverages

include $(MODULE_TOPDIR)/include/Make/Script.make

default: script
	$(MAKE) $(ETC)/grass_write_ascii.style

$(ETC)/%: %
	$(INSTALL_DATA) $< $@
