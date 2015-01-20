MODULE_TOPDIR = ../..

PGM = i.spec.sam

LIBES     = $(IMAGERYLIB) $(GMATHLIB) $(RASTERLIB) $(GISLIB) -lmeschach
DEPENDENCIES= $(IMAGERYDEP) $(GMATHDEP) $(RASTERDEP) $(GISDEP)

EXTRA_INC =  -I/usr/include/meschach

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
