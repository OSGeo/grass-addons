MODULE_TOPDIR = ../../..

PGM = r.green.hydro

SUBDIRS = libhydro \
	r.green.hydro.theoretical  \
	r.green.hydro.planning  \
	r.green.hydro.technical    \
	r.green.hydro.financial    \
	r.green.hydro.closest      \
	r.green.hydro.optimal      \
	r.green.hydro.structure    \
	r.green.hydro.delplants    \
	r.green.hydro.discharge

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs
