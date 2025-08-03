MODULE_TOPDIR = ../..

PGM = r.massmov

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP)
#openMP support
EXTRA_CFLAGS=-fopenmp
EXTRA_LIBS=$(GISLIB) -lgomp $(MATHLIB)



include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
