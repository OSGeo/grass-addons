MODULE_TOPDIR = ../..
CC=mpicc --static
PGM = i.vi.mpi

LIBES = $(GISLIB) $(GMATHLIB)
DEPENDENCIES = $(GISDEP) $(GMATHDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

ifneq ($(USE_LARGEFILES),)
	EXTRA_CFLAGS = -D_FILE_OFFSET_BITS=64
endif

default: cmd
CC=mpicc
