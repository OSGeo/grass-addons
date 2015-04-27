MODULE_TOPDIR = ../../..

PGM=r.green.hydro

SUBDIRS = r.green.hydro.theoretical  \
          r.green.hydro.legal        \
          r.green.hydro.recommended  \
          r.green.hydro.economic     \
          r.green.hydro.closest      \
		  r.green.hydro.optimal      \
		  r.green.hydro.structure    \
		  r.green.hydro.delplants \
          libhydro

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
