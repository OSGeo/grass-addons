MODULE_TOPDIR = ../../..

PGM = r.dem.icp

LIBES = $(RASTERLIB) $(GISLIB) -lm
DEPENDENCIES = $(RASTERDEP) $(GISDEP)
EXTRA_CFLAGS = -fopenmp -O3 -std=c11
EXTRA_LIBS = -fopenmp

SOURCES = \
	main.c \
	icp.c \
	normals.c \
	resample.c \
	linalg.c \
	utils.c

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
