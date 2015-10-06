MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make

DSTDIR = $(ETC)/wx.metadata/config

XMLFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.xml))
TXTFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.txt))
HTMLFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.html))

default: $(XMLFILES) $(TXTFILES) $(HTMLFILES) 

install:
	$(MKDIR) $(INST_DIR)/etc/wx.metadata/config
	@cp -rL $(DSTDIR) $(INST_DIR)/etc/wx.metadata

$(DSTDIR):
	$(MKDIR) -p $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
