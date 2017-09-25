MODULE_TOPDIR = ../..

PGM = r.spread.sod

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB) $(VECTORLIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP) $(VECTORDEP)
EXTRA_LIBS = $(GDALLIBS) $(OMPLIB)
EXTRA_CFLAGS = $(GDALCFLAGS) $(OMPCFLAGS) $(VECT_CFLAGS) -std=c++11
EXTRA_INC = $(VECT_INC)

include $(MODULE_TOPDIR)/include/Make/Module.make

LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
