MODULE_TOPDIR = ../../..

EXTRA_LIBS=$(GISLIB) $(MATHLIB)

LIB_NAME = grass_rpi.$(GRASS_LIB_VERSION_NUMBER)

LIB_OBJS := $(subst .c,.o,$(wildcard *.c))

DEPENDENCIES = $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Lib.make

default: lib
#	$(INSTALL_DATA) description.html $(GISBASE)/docs/html/r.pi.library.html
