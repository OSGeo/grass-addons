MODULE_TOPDIR = ../..

PGM = i.points.auto

LIBES     = $(IMAGERYLIB) $(GMATHLIB) $(D_LIB) $(DISPLAYLIB) $(RASTERLIB) $(GISLIB) $(VASKLIB) $(CURSES) $(FFTWLIB)
DEPENDENCIES= $(IMAGERYDEP) $(GMATHDEP) $(D_DEP) $(DISPLAYDEP) $(RASTERDEP) $(GISDEP) $(VASKDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd

# override html target as module doesn't use the standard parser
html:
	$(MKDIR) $(GISBASE)/docs/html
	$(INSTALL_DATA) description.html $(GISBASE)/docs/html/
