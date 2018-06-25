MODULE_TOPDIR = ../../../trunk

PGM = r.accumulate

LIBES = $(GISLIB) $(RASTERLIB) $(VECTORLIB)
DEPENDENCIES = $(GISDEP) $(RASTERDEP) $(VECTORDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
