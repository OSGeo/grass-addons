MODULE_TOPDIR = ../..

PGM1=init_db.sh
PGM2=r.rast4d.init
PGM3=tg.update
PGM4=tg.list
PGM5=tg.remove
PGM6=tg.decades.calc

include $(MODULE_TOPDIR)/include/Make/Script.make

default:
	$(INSTALL) ${PGM2} bin/${PGM3} bin/${PGM4} bin/${PGM5} bin/${PGM6} $(GISBASE)/scripts/
	if [ ! -d $(ETC)/r.rast4d ]; then $(MKDIR) $(ETC)/r.rast4d ; fi
	if [ ! -d $(ETC)/r.rast4d/globals ]; then $(MKDIR) $(ETC)/r.rast4d/globals ; fi
	if [ ! -d $(ETC)/r.rast4d/sql ]; then $(MKDIR) $(ETC)/r.rast4d/sql ; fi
	if [ ! -d $(ETC)/r.rast4d/lib ]; then $(MKDIR) $(ETC)/r.rast4d/lib ; fi
	if [ ! -d $(ETC)/r.rast4d/bin ]; then $(MKDIR) $(ETC)/r.rast4d/bin ; fi
	$(INSTALL) bin/${PGM1} $(ETC)/r.rast4d/bin/
	$(INSTALL) lib/*.sh $(ETC)/r.rast4d/lib
	$(INSTALL_DATA) globals/defines.sh $(ETC)/r.rast4d/globals/
	$(INSTALL_DATA) sql/create_* $(ETC)/r.rast4d/sql/
