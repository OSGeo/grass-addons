# MODULE_TOPDIR = ../..
MODULE_TOPDIR = /home/landa/src/grass6_devel

PGM = v.in.gama

LIBES = $(VECTLIB) $(GISLIB) `xml2-config --libs`
DEPENDENCIES= $(VECTDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS) `xml2-config --cflags`

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd xml

xml:
	if [ ! -d $(GISBASE)/etc ]; then $(MKDIR) $(GISBASE)/etc; fi
	if [ ! -d $(GISBASE)/etc/v.in.gama ]; then $(MKDIR) $(GISBASE)/etc/v.in.gama; fi
	$(INSTALL) -m 644 tables.xml $(GISBASE)/etc/v.in.gama/
