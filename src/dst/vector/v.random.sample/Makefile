MODULE_TOPDIR = ../..

PGM = v.random.sample

#GT_LIB_RAST = -lgt_raster
LIBES = $(GISLIB) $(DATETIMELIB) $(VECTLIB) $(GT_LIB_RAST) $(DBMILIB) $(GDALLIBS)
DEPENDENCIES = $(VECTDEP) $(GPROJDEP) $(DBMIDEP) $(GISDEP)
EXTRA_CFLAGS = -I../../include $(VECT_CFLAGS)
EXTRA_INC = $(VECT_INC) $(PROJINC)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
