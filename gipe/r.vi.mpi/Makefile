MODULE_TOPDIR = ../..
CC=mpicc --static
PGM = r.vi.mpi

LIBES = $(GISLIB) $(GMATHLIB)
DEPENDENCIES = $(GISDEP) $(GMATHDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
CC=mpicc
