MODULE_TOPDIR = ../..


PGM = i.vi.mpi

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
CC = mpicc
