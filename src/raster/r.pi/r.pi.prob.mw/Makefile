MODULE_TOPDIR = ../../..

PGM = r.pi.prob.mw

LIB_NAME = grass_rpi.$(GRASS_LIB_VERSION_NUMBER)
RPI_LIB  = -l$(LIB_NAME)

LIBES = $(STATSLIB) $(RASTERLIB) $(GISLIB) $(RPI_LIB)
DEPENDENCIES = $(STATSDEP) $(RASTERDEP) $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
