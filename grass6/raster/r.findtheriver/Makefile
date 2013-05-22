# fix this relative to include/
# or use absolute path to the GRASS source code
MODULE_TOPDIR = ../..
GRASS_VERSION_STR = 6.4

PGM = r.findtheriver

COMPILE_FLAGS = -g -Wall -Werror-implicit-function-declaration -fno-common
LIBES = $(GISLIB)
DEPENDENCIES = $(GISDEP)

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd

deploy:
	cp dist.*/bin/$(PGM) /Library/GRASS/$(GRASS_VERSION_STR)/Modules/bin
	cp dist.*/docs/html/* /Library/GRASS/$(GRASS_VERSION_STR)/Modules/docs/html