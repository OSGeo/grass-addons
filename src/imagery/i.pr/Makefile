MODULE_TOPDIR = ../..

PGM = i.pr

include $(MODULE_TOPDIR)/include/Make/Dir.make

SUBDIRS = \
        PRLIB \
	i.pr.blob \
	i.pr.classify \
	i.pr.features \
	i.pr.features_additional \
	i.pr.features_extract \
	i.pr.features_selection \
	i.pr.model \
	i.pr.subsets \
	i.pr.uxb \
	i.pr.sites_aggregate

# currently unsupported
# i.pr.statistics
# i.pr.training

default: subdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
