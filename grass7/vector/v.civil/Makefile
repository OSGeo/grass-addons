# fix this relative to include/
# or use absolute path to the GRASS source code

MODULE_TOPDIR = ../..
PGM = v.civil

ETCFILES = road_road road_base road_plant road_vertical road_displ \
	   road_terr road_profiles road_trans road_tables road_marks \
	   road_crosstools road_topotools

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

default: script
