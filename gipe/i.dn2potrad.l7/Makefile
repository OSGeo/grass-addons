MODULE_TOPDIR = ../..

PGM = i.dn2potrad.l7

LIBES = $(GPROJLIB) $(GISLIB) $(OPENMP)
DEPENDENCIES = $(GPROJDEP) $(GISDEP)
EXTRA_INC = $(PROJINC)

include $(MODULE_TOPDIR)/include/Make/Module.make

ifneq ($(USE_LARGEFILES),)
	EXTRA_CFLAGS = -D_FILE_OFFSET_BITS=64
endif

default: cmd
