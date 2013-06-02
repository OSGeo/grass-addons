MODULE_TOPDIR = ../..

PGM = v.ten

LIBES = $(VECTORLIB) $(GISLIB)
DEPENDENCIES = $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

EXTRA_CFLAGS = -frounding-math
EXTRA_LDFLAGS = -lCGAL -lgmp
LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
