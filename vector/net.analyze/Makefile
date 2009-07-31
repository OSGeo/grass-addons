MODULE_TOPDIR = ../..

SUBDIRS1 = \
	v.net.components \
        v.net.bridge \
        v.net.spanningtree \
        v.net.allpairs \
        v.net.flow \
        v.net.connectivity \
        v.net.centrality \
        v.net.distance \
        v.net.timetable

SUBDIRS = netalib $(SUBDIRS1)

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

clean: cleansubdirs

$(SUBDIRS1): netalib

