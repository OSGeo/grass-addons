MODULE_TOPDIR = ../..

PGM = i.spec.convexhull

LIBES = $(IMAGERYLIB) $(RASTERLIB) $(GISLIB)
DEPENDENCIES = $(IMAGERYDEP) $(RASTERDEP) $(GISDEP)

EXTRA_CFLAGS = -fopenmp
EXTRA_LIBS = -fopenmp

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
