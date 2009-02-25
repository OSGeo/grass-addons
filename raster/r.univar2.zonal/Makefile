
MODULE_TOPDIR = ../..

LIBES = $(G3DLIB) $(GISLIB)
DEPENDENCIES = $(G3DDEP) $(GISDEP)

#needed for htmlmulti
PROGRAMS = r.univar.zonal r3.univar.zonal

include $(MODULE_TOPDIR)/include/Make/Multi.make

R3UNIVAR = $(BIN)/r3.univar.zonal$(EXE)
RUNIVAR = $(BIN)/r.univar.zonal$(EXE)

default: $(RUNIVAR) $(R3UNIVAR)
	$(MAKE) htmlmulti

$(RUNIVAR): $(OBJDIR)/r.univar_main.o $(OBJDIR)/sort.o $(OBJDIR)/stats.o
	$(CC) $(LDFLAGS) -o $@ $^ $(FMODE_OBJ) $(LIBES) $(XDRLIB) $(MATHLIB)

$(R3UNIVAR): $(OBJDIR)/r3.univar_main.o $(OBJDIR)/sort.o $(OBJDIR)/stats.o
	$(CC) $(LDFLAGS) -o $@ $^ $(FMODE_OBJ) $(LIBES) $(XDRLIB) $(MATHLIB)

