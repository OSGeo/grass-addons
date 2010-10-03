MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make
include $(MODULE_TOPDIR)/include/Make/Doxygen.make

SUBDIRS = python

default: subdirs
#	@echo "Please run 'make' in the individual subdirectories"

# doxygen:
DOXNAME=swig
