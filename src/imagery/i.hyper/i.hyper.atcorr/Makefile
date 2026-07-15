MODULE_TOPDIR = ../..

PGM = i.hyper.atcorr

# libsixsv sources are compiled directly into the module
L6S_SRCS := $(sort $(wildcard ../libsixsv/src/*.c))

EXTRA_INC     = -I../libsixsv/include -I../libsixsv/src
EXTRA_CFLAGS  = -O3 -ffast-math $(OPENMP_CFLAGS) -std=c11 \
                -Wall -Wextra -Wno-unused-parameter
EXTRA_LDFLAGS = $(OPENMP_LIBPATH) $(OPENMP_LIB) -lgomp
LIBES         = $(RASTER3DLIB) $(RASTERLIB) $(GISLIB) $(MATHLIB)

MOD_OBJS = main.o $(notdir $(L6S_SRCS:.c=.o))

include $(MODULE_TOPDIR)/include/Make/Module.make

# Find libsixsv sources via vpath so MOD_OBJS auto-detection works
vpath %.c ../libsixsv/src

default: cmd
