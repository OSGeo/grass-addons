MODULE_TOPDIR = ../..

PGM = i.segment

LIBES = $(IMAGERYLIB) $(RASTERLIB) $(SEGMENTLIB) $(GISLIB)
# $(LINKMLIB) 
DEPENDENCIES = $(IMAGERYDEP) $(RASTERDEP) $(SEGMENTDEP) $(GISDEP)
# $(LINKMLIB)

# Tried adding above two items.  Compile error:
# make: *** No rule to make target `-lgrass_linkm.7.0.svn', needed by `/home/emomsen/SVN/grass_trunk/dist.x86_64-unknown-linux-gnu/bin/i.segment'.  Stop.

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd

# included in very different way here:
# ... grass_trunk/lib/bitmap$ cat Makefile
#
