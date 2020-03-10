MODULE_TOPDIR =../..

PGM = r.futures

# note: to deactivate a module, just place a file "DEPRECATED" into the subdir
ALL_SUBDIRS := ${sort ${dir ${wildcard */.}}}
DEPRECATED_SUBDIRS := ${sort ${dir ${wildcard */DEPRECATED}}}
RM_SUBDIRS := bin/ docs/ etc/ scripts/
SUBDIRS_1 := $(filter-out $(DEPRECATED_SUBDIRS), $(ALL_SUBDIRS))
SUBDIRS := $(filter-out $(RM_SUBDIRS), $(SUBDIRS_1))

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(HTMLDIR)/$(PGM).html $(INST_DIR)/docs/html/
	$(eval IMG := $(wildcard $(HTMLDIR)/*.png) $(wildcard $(HTMLDIR)/*.jpg))
	if [ -n "$(IMG)" ] ; then \
		$(INSTALL_DATA) $(IMG)  $(INST_DIR)/docs/html/ ; \
	fi
	$(INSTALL_DATA) $(ARCH_DISTDIR)/docs/man/man1/$(PGM).1 $(INST_DIR)/docs/man/man1/
