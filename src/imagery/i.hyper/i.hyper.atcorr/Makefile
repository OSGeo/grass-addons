MODULE_TOPDIR = ../..

PGM = i.hyper.atcorr

# libsixsv sources are compiled directly into the module
L6S_SRCS := $(sort $(wildcard libsixsv/src/*.c))

EXTRA_INC     = -Ilibsixsv/include -Ilibsixsv/src $(OPENMP_INCPATH)
EXTRA_CFLAGS  = $(OPENMP_CFLAGS)
EXTRA_LIBS    = $(OPENMP_LIBPATH) $(OPENMP_LIB)
LIBES         = $(RASTER3DLIB) $(RASTERLIB) $(GISLIB) $(MATHLIB)

MOD_OBJS = main.o $(notdir $(L6S_SRCS:.c=.o))

include $(MODULE_TOPDIR)/include/Make/Module.make

# Find libsixsv sources via vpath so MOD_OBJS auto-detection works
vpath %.c libsixsv/src

default: cmd
