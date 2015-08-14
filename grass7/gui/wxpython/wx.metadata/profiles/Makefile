MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make

DSTDIR = $(ETC)/wx.metadata/profiles

$(DSTDIR):
	$(MKDIR) -p $@

default:

install: $(DSTDIR)
	$(INSTALL_DATA) *.xml $(DSTDIR)