MODULE_TOPDIR = ../../../grass

PGM = g.xremove

LIBES = $(GISLIB) $(VECTLIB) $(G3DLIB)
DEPENDENCIES = $(GISDEP) $(VECTDEP) $(G3DDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
