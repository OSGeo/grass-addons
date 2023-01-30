MODULE_TOPDIR = ../../..

PGM = r.green.biomassfor

SUBDIRS = libforest\
	  r.green.biomassfor.financial \
          r.green.biomassfor.theoretical \
          r.green.biomassfor.recommended \
          r.green.biomassfor.technical \
          r.green.biomassfor.legal \
          r.green.biomassfor.impact \
          r.green.biomassfor.co2

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(PGM).html $(INST_DIR)/docs/html/
