# MODULE_TOPDIR = ../../../../grass-latest-src
MODULE_TOPDIR = ../..

PGM = r.stone

# WHILE IN DEBUG MODE, TO BE REMOVED
EXTRA_CFLAGS = -g -O0

LIBES = $(GISLIB) $(RASTERLIB)
DEPENDENCIES = $(GISDEP) $(RASTERDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
