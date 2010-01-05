# fix this relative to include/
# or use absolute path to the GRASS source code
MODULE_TOPDIR = ../..

PGM = r.stream.basins

LIBES     = $(VECTLIB) $(DBMILIB) $(GISLIB)
DEPENDENCIES = $(VECTDEP) $(DBMIDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS) 
DEPENDENCIES = $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd

