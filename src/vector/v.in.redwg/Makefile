MODULE_TOPDIR = ../..

PGM = v.in.redwg

## hard coded
LIBREDWGLIB=-lredwg
#LIBREDWGLIBPATH=-L/usr/local/lib
#LIBREDWGINCPATH=-I/usr/local/include

DEPENDENCIES = $(VECTORDEP) $(DBMIDEP) $(GISDEP)
LIBES     = $(VECTORLIB) $(DBMILIB) $(GISLIB) $(LIBREDWGLIBPATH) $(LIBREDWGLIB)
EXTRA_INC = $(VECT_INC) $(LIBREDWGINCPATH)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

#ifneq ($(USE_LIBREDWG),)
default: cmd
#endif
