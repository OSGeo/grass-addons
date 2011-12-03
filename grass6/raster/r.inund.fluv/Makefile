MODULE_TOPDIR = ../..
PGM = r.inund.fluv

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Module.make

default: DIR $(ETC)/fortran_code/$(PGM) html 

DIR:
	mkdir -p $(ETC)/fortran_code/

$(ETC)/fortran_code/$(PGM): $(OBJ)
	gfortran -O1 -o find_main_channel find_main_channel.f90 
	gfortran -O1 -o clean_inundation clean_inundation.f90
	gfortran -O1 -o 2d_path 2d_path.f90
	gfortran -O1 -o correction_from_path correction_from_path.f90
	$(INSTALL) find_main_channel$(EXE)	$(ETC)/fortran_code/
	$(INSTALL) clean_inundation$(EXE) $(ETC)/fortran_code/
	$(INSTALL) 2d_path$(EXE) $(ETC)/fortran_code/
	$(INSTALL) correction_from_path$(EXE) $(ETC)/fortran_code/
	$(INSTALL) dati.mod $(ETC)/fortran_code/
	$(INSTALL) dd.mod $(ETC)/fortran_code/
	$(INSTALL) $(PGM) $(GISBASE)/scripts/


html:
	$(MKDIR) $(GISBASE)/docs/html
	$(INSTALL_DATA) $(PGM).html $(GISBASE)/docs/html/

clean:
	-rm -f find_main_channel$(EXE) clean_inundation$(EXE) 2d_path$(EXE) correction_from_path$(EXE) dati.mod dd.mod
