MODULE_TOPDIR = ../../..

include $(MODULE_TOPDIR)/include/Make/Platform.make

ifeq ($(GRASS_VERSION_MAJOR), 7)
FILES := $(wildcard *.html)

include $(MODULE_TOPDIR)/include/Make/Other.make
else
HTML_SOURCES := $(wildcard *.html)
HTML_FILES := $(filter-out $(wildcard *.tmp.html),$(HTML_SOURCES))
FILES := $(subst .html,,$(HTML_FILES))

include $(MODULE_TOPDIR)/include/Make/Grass.make
include $(MODULE_TOPDIR)/include/Make/Rules.make
endif

ifeq ($(GRASS_VERSION_MAJOR), 7)
default: $(patsubst %,$(HTMLDIR)/%,$(FILES))
else
default:
	for file in $(FILES) ; do \
	    rm -f $$file.tmp.html ; \
	    rm -f "$(GISBASE)/docs/html/$$file.html"; \
	    $(MAKE) htmldir PGM=$$file; \
	done
endif
