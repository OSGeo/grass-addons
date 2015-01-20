MODULE_TOPDIR = ../..

PGM = i.spec.sam

EXTRALIB = meschach.a
LIBES     = $(IMAGERYLIB) $(GMATHLIB) $(RASTERLIB) $(GISLIB)  
DEPENDENCIES= $(IMAGERYDEP) $(GMATHDEP) $(RASTERDEP) $(GISDEP)

EXTRA_INC =  $(VECT_INC) $(PROJINC)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
