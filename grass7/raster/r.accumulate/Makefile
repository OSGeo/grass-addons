MODULE_TOPDIR = ../../../trunk

PGM = r.accumulate

LIBES = $(RASTERLIB) $(VECTORLIB) $(GISLIB)
DEPENDENCIES = $(RASTERDEP) $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
