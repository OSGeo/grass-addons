
MODULE_TOPDIR = ..

# display gui misc
SUBDIRS := $(shell find ./ -maxdepth 2 -mindepth 2 -name "Makefile" -exec dirname {} \; | xargs -I {} basename {} )

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs
