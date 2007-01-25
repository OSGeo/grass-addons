MODULE_TOPDIR = ..

include $(MODULE_TOPDIR)/include/Make/Dir.make

SUBDIRS1 = \
	i.ask \
	i.atcorr \
	i.class \
	i.cluster \
	i.find \
	i.gensig \
	i.gensigset \
	i.group \
	i.his.rgb \
	i.maxlik \
	i.ortho.photo \
	i.points \
	i.rectify \
	i.rgb.his \
	i.smap \
	i.target \
	i.vpoints \
	i.pca \
	i.cca

FFTWBASED = i.fft i.ifft i.zc

#compile if FFTW present:
ifneq ($(strip $(FFTWLIB)),)
    SUBDIRS2 = $(SUBDIRS1) $(FFTWBASED)
else
    SUBDIRS2 = $(SUBDIRS1)
endif

SUBDIRS = $(SUBDIRS2)

default: subdirs htmldir

clean: cleansubdirs

PGM = imageryintro
