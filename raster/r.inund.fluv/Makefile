MODULE_TOPDIR = ../..

PGM = r.inund.fluv

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Module.make


default: DIR $(ETC)/fortran_code/$(PGM) html

DIR:
	mkdir -p  $(MODULE_TOPDIR)/etc/fortran_code/

$(ETC)/fortran_code/$(PGM): $(OBJ)
	gfortran -O1 -o find_main_channel.exe find_main_channel.f90 
	gfortran -O1 -o clean_inundation.exe clean_inundation.f90
	gfortran -O1 -o 2d_path.exe 2d_path.f90
	gfortran -O1 -o correction_from_path.exe correction_from_path.f90
	$(INSTALL) find_main_channel.exe $(MODULE_TOPDIR)/etc/fortran_code
	$(INSTALL) clean_inundation.exe $(MODULE_TOPDIR)/etc/fortran_code
	$(INSTALL) 2d_path.exe $(MODULE_TOPDIR)/etc/fortran_code
	$(INSTALL) correction_from_path.exe $(MODULE_TOPDIR)/etc/fortran_code
	$(INSTALL) dati.mod $(MODULE_TOPDIR)/etc/fortran_code
	$(INSTALL) dd.mod $(MODULE_TOPDIR)/etc/fortran_code
	$(INSTALL) $(PGM) $(MODULE_TOPDIR)/scripts/

html:
	$(MKDIR) $(MODULE_TOPDIR)/docs/html
	$(INSTALL_DATA) $(PGM).html $(MODULE_TOPDIR)/docs/html/

clean:
	-rm -f find_main_channel.exe clean_inundation.exe 2d_path.exe correction_from_path.exe dati.mod dd.mod