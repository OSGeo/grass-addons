MODULE_TOPDIR = ../..

PGM = i.spec.sam

EXTRALIB = meschach.a
EXTRA_INC = $(PROJINC)
LIBES     = $(IMAGERYLIB) $(GMATHLIB) $(RASTERLIB) $(GISLIB)  
DEPENDENCIES= $(IMAGERYDEP) $(GMATHDEP) $(RASTERDEP) $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
