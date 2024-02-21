MODULE_TOPDIR = ../..

ifeq '$(findstring ;,$(PATH))' ';'
    detected_OS := Windows
else
    detected_OS := $(shell uname 2>/dev/null || echo Unknown)
    detected_OS := $(patsubst CYGWIN%,Cygwin,$(detected_OS))
    detected_OS := $(patsubst MSYS%,MSYS,$(detected_OS))
    detected_OS := $(patsubst MINGW%,MSYS,$(detected_OS))
endif

PGM = v.delaunay3d

LIBES = $(GPROJLIB) $(VECTORLIB) $(GISLIB)
DEPENDENCIES = $(GPROJDEP) $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC) $(PROJINC)
EXTRA_CFLAGS = $(VECT_CFLAGS) -frounding-math
ifeq ($(detected_OS),FreeBSD)
EXTRA_LDFLAGS = -lgmp -lcxxrt -lstdc++
else
EXTRA_LDFLAGS = -lgmp -lstdc++
endif

LINK = $(CXX)

include $(MODULE_TOPDIR)/include/Make/Module.make

ifneq ($(strip $(CXX)),)
default: cmd
endif
