MODULE_TOPDIR = ../..

ETCDIR = $(ETC)/wxpython

PGM = v.krige.py

include $(MODULE_TOPDIR)/include/Make/Script.make

default: script
	$(MKDIR) ${ETCDIR}/scripts/
	${INSTALL} v_krige_wxGUI.py ${ETCDIR}/scripts/
