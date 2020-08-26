MODULE_TOPDIR = ..

SHELL_OUTPUT := $(shell python mdlib/dependency.py 2>&1)
ifeq ($(filter File mdlib/dependency.py,$(SHELL_OUTPUT)),)
    $(info $(SHELL_OUTPUT))
else
    $(error $(SHELL_OUTPUT))
endif

SUBDIRS = \
    mdlib \
    profiles \
    config \
    r.info.iso \
    v.info.iso \
    t.info.iso \
    db.csw.admin \
    db.csw.run \
    db.csw.harvest \
    g.gui.cswbrowser \
    g.gui.metadata \
    m.csw.update

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs

install: installsubdirs
