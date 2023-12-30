MODULE_TOPDIR = ../..

PGM = i.spec.sam

LIBES        = $(GISLIB) $(GMATHLIB) $(IMAGERYLIB) $(RASTERLIB)
DEPENDENCIES = $(GISDEP) $(GMATHDEP) $(IMAGERYDEP) $(RASTERDEP)

EXTRA_CFLAGS = -fopenmp
EXTRA_LIBS   = -lgomp

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
