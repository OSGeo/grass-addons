
MODULE_TOPDIR = ../..

LIBES2 = $(RASTERLIB) $(GISLIB) $(MATHLIB)
LIBES3 = $(G3DLIB) $(GISLIB) $(MATHLIB)
DEPENDENCIES = $(G3DDEP) $(GISDEP) $(RASTERDEP)

PROGRAMS = r.univar.zonal r3.univar.zonal

r_univar_zonal_OBJS = r.univar_main.o sort.o stats.o
r3_univar_zonal_OBJS = r3.univar_main.o sort.o stats.o

include $(MODULE_TOPDIR)/include/Make/Multi.make

default: multi

$(BIN)/r.univar.zonal$(EXE): LIBES = $(LIBES2)
$(BIN)/r3.univar.zonal$(EXE): LIBES = $(LIBES3)
