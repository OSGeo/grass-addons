MODULE_TOPDIR = ../..

PGM = m.dst.create

XMLLIB = `xml2-config --libs`
LIBES = $(GISLIB) $(DATETIMELIB) $(XMLLIB)
EXTRA_CFLAGS+=`xml2-config --cflags`

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
