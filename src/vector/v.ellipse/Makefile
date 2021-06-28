# fix this relative to include/
# or use absolute path to the GRASS source code
MODULE_TOPDIR = ../..

PGM = v.ellipse

LIBES = $(VECTORLIB) $(DBMILIB) $(GISLIB) $(MATHLIB) $(GMATHLIB)
DEPENDENCIES = $(VECTORDEP) $(DBMIDEP) $(GISDEP) $(GMATHDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
