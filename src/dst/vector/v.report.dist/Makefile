MODULE_TOPDIR = ../..

PGM = v.report.dist

GT_LIB_RAST = -lgt_raster
GT_LIB_STAT = -lgt_stats
GSL_LIB = `gsl-config --libs`
GSL_INC = `gsl-config --cflags`
LIBES = $(GISLIB) $(DATETIMELIB) $(VECTLIB) $(GSL_LIB) $(GT_LIB_RAST) $(GT_LIB_STAT) $(DBMILIB) $(GDALLIBS)
DEPENDENCIES = $(VECTDEP) $(GPROJDEP) $(DBMIDEP) $(GISDEP)
EXTRA_CFLAGS = -I../../include $(GSL_INC) $(VECT_CFLAGS)
EXTRA_INC = $(VECT_INC) $(PROJINC)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
