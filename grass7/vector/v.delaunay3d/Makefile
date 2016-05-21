MODULE_TOPDIR = /usr/lib/grass70

PGM = v.delaunay3d

LIBES = $(GPROJLIB) $(VECTORLIB) $(GISLIB)
DEPENDENCIES = $(GPROJDEP) $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC) $(PROJINC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

EXTRA_CFLAGS = -frounding-math
EXTRA_LDFLAGS = -lCGAL -lgmp
LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
