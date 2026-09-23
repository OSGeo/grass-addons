MODULE_TOPDIR = ../../..

PGM = r.dem.icp

LIBES = $(RASTERLIB) $(GISLIB) $(MATHLIB)
DEPENDENCIES = $(RASTERDEP) $(GISDEP)
EXTRA_CFLAGS = $(OPENMP_CFLAGS)
EXTRA_INC = $(OPENMP_INCPATH)
EXTRA_LIBS = $(OPENMP_LIBPATH) $(OPENMP_LIB)

SOURCES = \
	main.c \
	icp.c \
	normals.c \
	resample.c \
	linalg.c \
	utils.c

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
