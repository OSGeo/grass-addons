MODULE_TOPDIR = ../..

include $(MODULE_TOPDIR)/include/Make/Vars.make

PGM = v.feature.algebra

LIBES = $(VECTORLIB) $(GISLIB) $(DLLIB) $(MATHLIB)
DEPENDENCIES = $(VECTORDEP) $(GISDEP)
EXTRA_INC = $(VECT_INC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

HTMLSRC=

default: cmd

$(OBJDIR)/v.mapcalc.tab.o: v.mapcalc.tab.h

$(OBJDIR)/yylex.o: v.mapcalc.tab.h

.INTERMEDIATE: v.mapcalc.tab.c v.mapcalc.tab.h v.mapcalc.output
