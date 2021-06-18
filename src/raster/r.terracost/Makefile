MODULE_TOPDIR = ../..

PGM = r.terracost

MOD_OBJS = $(subst .cc,.o,$(wildcard *.cc))

include $(MODULE_TOPDIR)/include/Make/Module.make

LIBES = $(GISLIB) $(IOSTREAMLIB)
DEPENDENCIES = $(GISDEP) $(IOSTREAMDEP)

default: cmd

$(BIN)/$(PGM)$(EXE): $(ARCH_CMD_OBJS) $(DEPENDENCIES) 
	$(CXX) $(LDFLAGS) $(IOSTREAMFLAG) $(XTRA_LDFLAGS) $(EXTRA_CFLAGS) $(NLS_CFLAGS) -o $@ $(ARCH_CMD_OBJS) $(FMODE_OBJ) $(MATHLIB) $(XDRLIB) $(LIBES)
