MODULE_TOPDIR =../..

PGM = r.agent.aco

SUBDIRS = r.agent.aco \
			r.agent.rand \
			libagent

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: script parsubdirs

install: installsubdirs
		$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
