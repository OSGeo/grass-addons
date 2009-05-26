MODULE_TOPDIR = ../..

PGM=ps.output

LIBES     = $(VECTLIB) $(GPROJLIB) $(SYMBLIB) $(GISLIB) $(DATETIMELIB) $(IMAGERYLIB) $(GMATHLIB)
DEPENDENCIES = $(VECTDEP) $(SYMBDEP) $(GISDEP) $(DATETIDEP) $(IMAGERYDEP) $(GMATHDEP) \
               colors.h fonts.h lines.h frames.h ps_info.h local_proto.h

EXTRA_INC = $(VECT_INC) $(PROJINC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
