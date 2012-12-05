MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Module.make

LIBES        = $(GISLIB) $(GMATHLIB)
DEPENDENCIES = $(GISDEP) $(GMATHDEP)

PGM = gmath_test

default: $(ETC)/$(PGM)

$(ETC)/$(PGM): gmath_test.c
	$(CC) -c $<
	$(CC) -o $(ETC)/$(PGM) $<

clean:
	\rm -f $(ETC)/$(PGM) gmath_test.o
