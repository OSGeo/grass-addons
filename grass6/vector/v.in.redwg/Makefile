MODULE_TOPDIR = ../..

PGM=v.in.redwg

## hard coded
LIBREDWGLIB=-lredwg
#LIBREDWGLIBPATH=/usr/local/lib
#LIBREDWGINCPATH=/usr/local/include/dwg.h

DEPENDENCIES = $(VECTDEP) $(DBMIDEP) $(GISDEP)
LIBES     = $(VECTLIB) $(DBMILIB) $(GISLIB) $(LIBREDWGLIBPATH) $(LIBREDWGLIB)
EXTRA_INC = $(VECT_INC) $(LIBREDWGINCPATH)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

#ifneq ($(USE_LIBREDWG),)
default: cmd
#endif

