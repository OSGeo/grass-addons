MODULE_TOPDIR = ../..

PGM = r.evapo.PM

LIBES = $(GISLIB)
DEPENDENCIES = $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
