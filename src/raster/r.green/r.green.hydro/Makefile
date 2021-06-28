MODULE_TOPDIR = ../../..

PGM = r.green.hydro

# note: to deactivate a module, just place a file "DEPRECATED" into the subdir
ALL_SUBDIRS := ${sort ${dir ${wildcard */.}}}
DEPRECATED_SUBDIRS := ${sort ${dir ${wildcard */DEPRECATED}}}
RM_SUBDIRS := bin/ docs/ etc/ scripts/
SUBDIRS_1 := $(filter-out $(DEPRECATED_SUBDIRS), $(ALL_SUBDIRS))
SUBDIRS := $(filter-out $(RM_SUBDIRS), $(SUBDIRS_1))

SUBDIRS = libhydro \
	r.green.hydro.closest \
	r.green.hydro.delplants \
	r.green.hydro.discharge \
	r.green.hydro.financial \
	r.green.hydro.optimal \
	r.green.hydro.planning \
	r.green.hydro.recommended \
	r.green.hydro.structure \
	r.green.hydro.technical \
	r.green.hydro.theoretical

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
