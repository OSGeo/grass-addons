MODULE_TOPDIR = ../..

PGM = r.pops.spread

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB) $(VECTORLIB) $(DATETIMELIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP) $(VECTORDEP) $(DATETIMEDEP)
EXTRA_LIBS = $(GDALLIBS) $(OMPLIB)
EXTRA_CFLAGS = $(GDALCFLAGS) -std=c++11 -Wall -Wextra -fpermissive $(OMPCFLAGS) $(VECT_CFLAGS)
EXTRA_INC = $(VECT_INC)

include $(MODULE_TOPDIR)/include/Make/Module.make

LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
