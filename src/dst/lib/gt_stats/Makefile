MODULE_TOPDIR = ../..

GSL_LIB = `gsl-config --libs`
GSL_INC = `gsl-config --cflags`
LIB_NAME = gt_stats
LIB_OBJS = gstats_tests.o gstats_gain.o gstats_error.o
EXTRA_CFLAGS = -I../../include $(GSL_INC)
EXTRA_LIBS=$(GISLIB) $(GSL_LIB) 		

include $(MODULE_TOPDIR)/include/Make/Lib.make

default: lib headers

headers:
	if [ ! -d $(GISBASE)/include ]; then $(MKDIR) $(GISBASE)/include; fi
	if [ ! -d $(GISBASE)/include/gt ]; then $(MKDIR) $(GISBASE)/include/gt; fi
	$(INSTALL) -m 644 ../../include/gt/*.h $(GISBASE)/include/gt/
