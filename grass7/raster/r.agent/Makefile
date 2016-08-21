MODULE_TOPDIR =../..

PGM = r.agent

SUBDIRS = libagent \
	r.agent.aco \
	r.agent.rand

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
