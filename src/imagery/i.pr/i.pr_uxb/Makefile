MODULE_TOPDIR = ../../..

PRINCLUDE = ../include/
EXTRA_CFLAGS = -I$(PRINCLUDE)
PRLIB = -lgrass_pr.$(GRASS_LIB_VERSION_NUMBER)

PGM = i.pr.uxb

LIBES     = $(PRLIB) $(IMAGERYLIB) $(D_LIB) $(DISPLAYLIB) $(RASTERLIB) $(GISLIB) $(DATETIMELIB)
DEPENDENCIES= $(PRDEP) $(IMAGERYDEP) $(D_DEP) $(DISPLAYDEP) $(RASTERDEP) $(GISDEP) $(DATETIMEDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
