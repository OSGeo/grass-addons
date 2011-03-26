MODULE_TOPDIR = ../../..

HTML_SOURCES := $(wildcard *.html)
HTML_FILES := $(filter-out $(wildcard *.tmp.html),$(HTML_SOURCES))
FILES := $(subst .html,,$(HTML_FILES))

include $(MODULE_TOPDIR)/include/Make/Platform.make
include $(MODULE_TOPDIR)/include/Make/Grass.make
include $(MODULE_TOPDIR)/include/Make/Rules.make

default:
	for file in $(FILES) ; do \
	    rm -f $$file.tmp.html ; \
	    rm -f "$(GISBASE)/docs/html/$$file.html"; \
	    $(MAKE) htmldir PGM=$$file; \
	done
