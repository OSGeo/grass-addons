MODULE_TOPDIR = ..

SHELL_OUTPUT := $(shell python dependency.py 2>&1)
ifeq ($(filter File dependency.py,$(SHELL_OUTPUT)),)
    $(info $(SHELL_OUTPUT))
else
    $(error $(SHELL_OUTPUT))
endif

SUBDIRS = \
    hdfswraper \
    hdfsgrass \
    hd.esri2vector \
    hd.db.connect \
    hd.hdfs.in.fs \
    hd.hdfs.in.vector \
    hd.hdfs.info \
    hd.hdfs.out.vector \
    hd.hive.csv.table \
    hd.hive.execute \
    hd.hive.info \
    hd.hive.json.table \
	hd.hive.load \
	hd.hive.select

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

install: installsubdirs
