MODULE_TOPDIR = ../..

PGM = v.nnstat

LIBES = $(VECTORLIB) $(DBMILIB) $(GISLIB) $(GMATHLIB) $(IOSTREAMLIB) $(MATHLIB) -lpcl_apps -lpcl_common -lpcl_features -lpcl_filters -lpcl_io -lpcl_kdtree -lpcl_keypoints -lpcl_octree -lpcl_registration -lpcl_sample_consensus -lpcl_search -lpcl_segmentation -lpcl_surface -lpcl_visualization
DEPENDENCIES= $(VECTORDEP) $(DBMIDEP) $(GISDEP) $(IOSTREAMDEP)
EXTRA_INC = $(VECT_INC) -I/usr/include/pcl-1.7 -I/usr/include/eigen3 $(PCL_INCLUDE_DIRS)
EXTRA_CFLAGS = $(VECT_CFLAGS)

include $(MODULE_TOPDIR)/include/Make/Module.make

LINK = $(CXX)

ifneq ($(strip $(CXX)),)
default: cmd
endif
