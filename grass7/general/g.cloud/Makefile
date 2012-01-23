MODULE_TOPDIR = ../..

PGM = g.cloud

include $(MODULE_TOPDIR)/include/Make/Script.make

SRCFILES = cloud_which.py cloud_ssh.py cloud_unpack.py cloud_collect.sh cloud_mail.sh
DSTFILES := $(patsubst %,$(ETC)/g.cloud/%,$(SRCFILES))

default: script $(DSTFILES)

$(ETC)/g.cloud/%: % | $(ETC)/g.cloud
	$(INSTALL) $< $@

$(ETC)/g.cloud:
	$(MKDIR) $@
