# fix this relative to include/
# or use absolute path to the GRASS source code
MODULE_TOPDIR = ../..

PGM = i.superpixels.slic

LIBES = $(IMAGERYLIB) $(RASTERLIB) $(SEGMENTLIB) $(GISLIB)
DEPENDENCIES = $(IMAGERYDEP) $(RASTERDEP) $(SEGMENTDEP) $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
