MODULE_TOPDIR = /home/evergreen/grass7

PGM = v.kriging

# other PCL version:
#-lpcl_apps -lpcl_common -lpcl_features -lpcl_filters -lpcl_io -lpcl_kdtree -lpcl_keypoints -lpcl_octree -lpcl_registration -lpcl_sample_consensus -lpcl_search -lpcl_segmentation -lpcl_surface -lpcl_visualization
LIBES = $(RASTER3DLIB) $(RASTERLIB) $(VECTORLIB) $(DBMILIB) $(GMATHLIB) $(GISLIB) $(IOSTREAMLIB)  $(RTREELIB)

DEPENDENCIES= $(RASTER3DDEP) $(RASTERDEP) $(VECTORDEP) $(DBMIDEP) $(GMATHDEP) $(GISDEP) $(IOSTREAMDEP) $(RTREEDEP)
EXTRA_INC = $(VECT_INC) -I/usr/include/pcl-1.7 -I/usr/include/eigen3 $(PCL_INCLUDE_DIRS) $(PROJINC)
EXTRA_CFLAGS = $(VECT_CFLAGS)

EXTRA_CFLAGS=-fopenmp
EXTRA_LIBS=$(GISLIB) -lgomp $(MATHLIB) -lboost_system

include $(MODULE_TOPDIR)/include/Make/Module.make

LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
