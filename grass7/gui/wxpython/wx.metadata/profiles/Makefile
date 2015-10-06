MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make

DSTDIR = $(ETC)/wx.metadata/profiles

XMLFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.xml))

default: $(XMLFILES)

install:
	$(MKDIR) $(INST_DIR)/etc/wx.metadata/profiles
	@cp -rL $(DSTDIR) $(INST_DIR)/etc/wx.metadata

$(DSTDIR):
	$(MKDIR) -p $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
