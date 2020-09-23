MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make

DSTDIR = $(ETC)/wx.metadata/config

XMLFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.xml))
XSDFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.xsd))
TXTFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.txt))
HTMLFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.html))
PNGFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.png))
CFGFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.cfg))
ODSFILES := $(patsubst %,$(DSTDIR)/%,$(wildcard *.ods))

default: $(XMLFILES) $(TXTFILES) $(HTMLFILES) $(PNGFILES) $(CFGFILES) \
	$(XSDFILES) $(ODSFILES)

install:
	$(MKDIR) $(INST_DIR)/etc/wx.metadata/config
	@cp -rL $(DSTDIR) $(INST_DIR)/etc/wx.metadata

$(DSTDIR):
	$(MKDIR) -p $@

$(DSTDIR)/%: % | $(DSTDIR)
	$(INSTALL_DATA) $< $@
