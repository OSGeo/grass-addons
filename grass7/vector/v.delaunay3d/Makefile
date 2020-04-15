MODULE_TOPDIR = ../..

PGM = v.delaunay3d

LIBES = $(GPROJLIB) $(VECTORLIB) $(GISLIB)
DEPENDENCIES = $(GPROJDEP) $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC) $(PROJINC)
EXTRA_CFLAGS = $(VECT_CFLAGS) -frounding-math
ifeq ($(shell uname -s),  FreeBSD)
EXTRA_LDFLAGS = -lCGAL -lgmp -lcxxrt -lstdc++
else
EXTRA_LDFLAGS = -lCGAL -lgmp -lstdc++
endif

LINK = $(CXX)

include $(MODULE_TOPDIR)/include/Make/Module.make

ifneq ($(strip $(CXX)),)
default: cmd
endif
