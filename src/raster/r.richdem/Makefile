MODULE_TOPDIR = ../..

PGM = r.richdem

SUBDIRS = \
    librichdem \
    r.richdem.filldepressions \
    r.richdem.breachdepressions \
    r.richdem.resolveflats \
    r.richdem.flowaccumulation \
    r.richdem.terrainattribute \
    r.richdem.dephier \
    r.richdem.fsm

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(HTMLDIR)/$(PGM).html $(INST_DIR)/docs/html/
