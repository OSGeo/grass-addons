MODULE_TOPDIR = ..

SUBDIRS = \
	mdlib \
	r.info.iso \
	v.info.iso \
	g.gui.metadata

include $(MODULE_TOPDIR)/include/Make/Dir.make

default:
	$(MAKE) parsubdirs

install:
	@cd mdlib ; $(MAKE) install
	@cd r.info.iso ; $(MAKE) install
	@cd v.info.iso ; $(MAKE) install
	@cd g.gui.metadata ; $(MAKE) install
