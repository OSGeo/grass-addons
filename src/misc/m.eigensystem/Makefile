MODULE_TOPDIR = ../..

PGM = m.eigensystem

include $(MODULE_TOPDIR)/include/Make/Module.make

default: $(BIN)/$(PGM) html

OBJ = main.o\
    balanc.o \
    balbak.o \
    cdiv.o \
    elmhes.o \
    eltran.o \
    hqr.o \
    hqr2.o \
    rg.o

$(BIN)/$(PGM): $(OBJ)
	$(FC) -o $@ $(OBJ)

clean:
	-rm -f *.o
