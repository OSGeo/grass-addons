MODULE_TOPDIR = ../..

SUBDIRS1 = \
	v.net.components \
        v.net.bridge \
        v.net.spanningtree

SUBDIRS = netalib $(SUBDIRS1)

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

clean: cleansubdirs

$(SUBDIRS1): netalib

