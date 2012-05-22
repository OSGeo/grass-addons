MODULE_TOPDIR = ../..

LIB_NAME = gt_vector
LIB_OBJS = gt_vector.o

EXTRA_LIBS = $(VECTLIB) $(DBMILIB) $(GISLIB)
DEPENDENCIES= $(VECTDEP) $(DBMIDEP) $(GISDEP) 
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = -I../../include $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Lib.make

default: lib headers

headers:
	if [ ! -d $(GISBASE)/include ]; then $(MKDIR) $(GISBASE)/include; fi
	if [ ! -d $(GISBASE)/include/gt ]; then $(MKDIR) $(GISBASE)/include/gt; fi
	$(INSTALL) -m 644 ../../include/gt/*.h $(GISBASE)/include/gt/
