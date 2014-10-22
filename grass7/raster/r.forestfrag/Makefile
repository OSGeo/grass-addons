MODULE_TOPDIR = ../..

PGM = r.forestfrag

include $(MODULE_TOPDIR)/include/Make/Script.make

default: install

install:
	$(INSTALL) $(PGM) $(INST_DIR)/scripts/
	$(INSTALL_DATA) $(HTMLDIR)/$(PGM).html $(INST_DIR)/docs/html/
	$(INSTALL_DATA) $(ARCH_DISTDIR)/docs/man/man1/$(PGM).1 $(INST_DIR)/docs/man/man1/
	if [ -d "$(ETC)/$(PGM)" -a "$(ls -A $(ETC)/$(PGM))" ] ; then \
		cp -rL $(ETC)/$(PGM) $(INST_DIR)/etc/ ; \
	fi

