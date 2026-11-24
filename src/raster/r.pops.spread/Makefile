MODULE_TOPDIR = ../..

PGM = r.pops.spread

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB) $(VECTORLIB) $(DATETIMELIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP) $(VECTORDEP) $(DATETIMEDEP)
EXTRA_LIBS = $(GDALLIBS) $(OPENMP_LIBPATH) $(OPENMP_LIB)
EXTRA_CFLAGS = $(GDALCFLAGS) -std=c++11 -Wall -Wextra -Werror=return-type -fpermissive $(OPENMP_CFLAGS) $(VECT_CFLAGS)
EXTRA_INC = $(VECT_INC) -Ipops-core/include

include $(MODULE_TOPDIR)/include/Make/Module.make

LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
