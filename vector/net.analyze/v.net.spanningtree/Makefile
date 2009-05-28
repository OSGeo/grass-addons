MODULE_TOPDIR = ../../..

PGM=v.net.spanningtree

include ../Netalib.make

LIBES     = $(NETALIB) $(VECTLIB) $(VECTLIB_REAL) $(DBMILIB) $(GISLIB)
DEPENDENCIES = $(NETADEP) $(VECTDEP) $(DBMIDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)
 
include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd	

