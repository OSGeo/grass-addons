### varseglib MAKEFILE ###

MODULE_TOPDIR = ../../..

LIB_NAME = $(SEG_LIBNAME)

LIB_OBJS = varseg.o

include ../include/Make/varseg.make

include $(MODULE_TOPDIR)/include/Make/Lib.make

include $(MODULE_TOPDIR)/include/Make/Doxygen.make

default: $(ARCH_INCDIR)/varseg.h lib

$(ARCH_INCDIR)/varseg.h: ../include/varseg/varseg.h
	$(INSTALL) -m 644 ../include/varseg/varseg.h $(ARCH_INCDIR)/varseg.h

#doxygen:
DOXNAME = varseg
