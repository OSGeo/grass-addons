MODULE_TOPDIR = ../..

PGM = r.dst.combine

GT_LIB_RAST = -lgt_raster
XML_LIB = `xml2-config --libs`
XML_INC = `xml2-config --cflags`
LIBES = $(GISLIB) $(DATETIMELIB) $(GT_LIB_RAST) $(XML_LIB)
EXTRA_CFLAGS = $(XML_INC) -I../../include -g -Wall -pedantic -Werror-implicit-function-declaration -fno-common

include $(MODULE_TOPDIR)/include/Make/Module.make

default: cmd
