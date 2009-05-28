MODULE_TOPDIR = ../../..

include ../Netalib.make

EXTRA_LIBS = $(VECTLIB) $(VECTLIB_REAL) $(DBMILIB) $(GISLIB) 
DEPENDENCIES= $(VECTDEP) $(DBMIDEP) $(GISDEP) 
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

LIB_NAME = $(NETA_LIBNAME)

include $(MODULE_TOPDIR)/include/Make/Lib.make

default: $(ARCH_INCDIR)/neta.h lib

$(ARCH_INCDIR)/neta.h: neta.h
	cp neta.h $(ARCH_INCDIR)/neta.h
