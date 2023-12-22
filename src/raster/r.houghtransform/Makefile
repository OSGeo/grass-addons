# fix this relative to include/
# or use absolute path to the GRASS source code
MODULE_TOPDIR = ../..

PGM = r.houghtransform

LIBES = $(VECTORLIB) $(GISLIB) $(RASTERLIB)  $(GMATHLIB)
DEPENDENCIES = $(VECTORDEP) $(GISDEP) $(RASTERDEP)

EXTRA_INC = $(VECT_INC)

include $(MODULE_TOPDIR)/include/Make/Module.make

EXTRA_CFLAGS = $(VECT_CFLAGS) -Wno-sign-compare -Wall -Wextra -O0 -Wconversion

LINK = $(CXX)

#ifneq ($(strip $(CXX)),)
default: cmd
#endif
