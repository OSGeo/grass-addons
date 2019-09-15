MODULE_TOPDIR = ..

# commands replaced with more modern commands in trunk/relbranch
OLD = \
	r.in.arc \
	r.out.arc \
	r.out.tiff \
#	r.le.patch \
#	r.le.pixel \
#	r.le.setup \
#	r.le.trace

# unclear
#	r.convert \

SUBDIRS := ${sort ${dir ${wildcard */.}}}

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: subdirs
