MODULE_TOPDIR = ../..

PGM = i.hyper.atcorr

SIXSVLIB = -lgrass_sixsv.$(GRASS_LIB_VERSION_NUMBER)

EXTRA_CFLAGS = -O3 -ffast-math $(OPENMP_CFLAGS) -std=c11 \
               -Wall -Wextra -Wno-unused-parameter
EXTRA_LDFLAGS = $(OPENMP_LIBPATH) $(OPENMP_LIB) -lgomp
LIBES = $(SIXSVLIB) $(RASTER3DLIB) $(RASTERLIB) $(GISLIB)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
