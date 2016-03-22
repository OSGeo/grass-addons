MODULE_TOPDIR =../..

PGM = r.futures

SUBDIRS = \
		r.futures.calib \
		r.futures.devpressure \
		r.futures.demand \
		r.futures.potential \
		r.futures.potsurface \
		r.futures.parallelpga \
		r.futures.pga

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
	$(INSTALL_DATA) $(HTMLDIR)/$(PGM).html $(INST_DIR)/docs/html/
	$(eval IMG := $(wildcard $(HTMLDIR)/*.png) $(wildcard $(HTMLDIR)/*.jpg))
	if [ -n "$(IMG)" ] ; then \
		$(INSTALL_DATA) $(IMG)  $(INST_DIR)/docs/html/ ; \
	fi
	$(INSTALL_DATA) $(ARCH_DISTDIR)/docs/man/man1/$(PGM).1 $(INST_DIR)/docs/man/man1/
