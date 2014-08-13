MODULE_TOPDIR = ..

SUBDIRS = \
	mdlib \
	r.info.iso \
	v.info.iso

include $(MODULE_TOPDIR)/include/Make/Dir.make

default:
	$(MAKE) parsubdirs

install:
	@cd mdlib ; $(MAKE) install
	@cd r.info.iso ; $(MAKE) install
	@cd v.info.iso ; $(MAKE) install
