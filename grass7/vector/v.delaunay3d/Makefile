MODULE_TOPDIR = ../..

PGM = v.delaunay3d

LIBES = $(GPROJLIB) $(VECTORLIB) $(GISLIB)
DEPENDENCIES = $(GPROJDEP) $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC) $(PROJINC)
EXTRA_CFLAGS = $(VECT_CFLAGS) -frounding-math
EXTRA_LDFLAGS = -lCGAL -lgmp -lstdc++ -lcxxrt
LINK = $(CXX)

include $(MODULE_TOPDIR)/include/Make/Module.make

ifneq ($(strip $(CXX)),)
default: cmd
endif
