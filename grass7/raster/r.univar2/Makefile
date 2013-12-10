
MODULE_TOPDIR = ../..

PGM = r.univar2

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB)
DEPENDENCIES = $(GISDEP) $(RASTERDEP)

PROGRAMS = r.univar2

r_univar_OBJS = r.univar_main.o sort.o stats.o

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
