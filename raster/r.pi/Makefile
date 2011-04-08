MODULE_TOPDIR = ..

SUBDIRS = \
	r.pi.corrwin \
	r.pi.export \
	r.pi.import \
	r.pi.index \
	r.pi.rectangle

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs
	$(INSTALL_DATA) description.html $(GISBASE)/docs/html/r.pi.html

clean: cleansubdirs
