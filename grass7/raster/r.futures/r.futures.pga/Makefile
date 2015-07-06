MODULE_TOPDIR = ../..

PGM = r.futures.pga

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

EXTRA_CFLAGS = -Wall

LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
