MODULE_TOPDIR = ../..

PROGRAMS = v.mainchannel r.strahler.sh r.broscoe.sh 

LIBES        = $(DISPLAYLIB) $(RASTERLIB) $(VECTLIB) $(GRAPHLIB) $(DBMILIB) $(GISLIB)
DEPENDENCIES = $(DISPLAYDEP) $(RASTERDEP) $(VECTDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Script.make

default: script

PGM = v.strahler

LIBES        = $(DISPLAYLIB) $(RASTERLIB) $(VECTLIB) $(GRAPHLIB) $(DBMILIB) $(GISLIB)
DEPENDENCIES = $(DISPLAYDEP) $(RASTERDEP) $(VECTDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
