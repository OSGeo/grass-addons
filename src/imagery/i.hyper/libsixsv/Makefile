MODULE_TOPDIR = ../../..

LIB_NAME = grass_sixsv.$(GRASS_LIB_VERSION_NUMBER)

EXTRA_INC = -Iinclude -Isrc
EXTRA_CFLAGS = -O3 -ffast-math -fopenmp -std=c11 -fPIC \
               -Wall -Wextra -Wno-unused-parameter

LIBES = $(OPENMP_LIBPATH) -lgomp $(MATHLIB)

include $(MODULE_TOPDIR)/include/Make/Lib.make

$(OBJDIR)/%.o: src/%.c | $(OBJDIR)
	$(call compiler_c)

default: lib
