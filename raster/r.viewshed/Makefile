# Path to the module directory, i.e. the grass sourcecode main path.
# Relative or absolute.
MODULE_TOPDIR = ../../

PGM = r.viewshed

# Includes the grass make-System.
include $(MODULE_TOPDIR)/include/Make/Module.make

SOURCES = main.cc distribute.cc eventlist.cc grid.cc grass.cc viewshed.cc \
	rbbst.cc statusstructure.cc visibility.cc
HEADERS = distribute.h eventlist.h grid.h grass.h viewshed.h \
	rbbst.h  statusstructure.h visibility.h


OBJARCH=OBJ.$(ARCH)
OBJ := $(patsubst %.cc,$(OBJARCH)/%.o,$(SOURCES))

LIBS = $(GISLIB) $(IOSTREAMLIB)
DEPLIBS = $(DEPGISLIB) $(IOSTREAMDEP)

# Using GNU c++ compiler.
CXX = g++

# Set compiler and load flags. 
# (See 'man g++' for help). 
CXXFLAGS += -O3 -DNO_STATS #-DNDEBUG
CXXFLAGS += $(WARNING_FLAGS)  -DUSER=\"$(USER)\" -D__GRASS__
# CXXFLAGS += -DPEARL 
CXXFLAGS += -D_FILE_OFFSET_BITS=64  -D_LARGEFILE_SOURCE   -fmessage-length=0
CXXFLAGS += -ffast-math -funroll-loops


WARNING_FLAGS   = -Wall -Wformat  -Wparentheses  -Wpointer-arith -Wno-conversion \
  -Wreturn-type	\
  -Wcomment  -Wno-sign-compare -Wno-unused
#-Wimplicit-int -Wimplicit-function-declaration

# Make rules.
# Default is the 'default' target for the grass make system.
$(OBJARCH)/%.o:%.cc
	$(CXX) -c $(CXXFLAGS)  $< -o $@


default: $(BIN)/$(PGM)$(EXE)
	$(MAKE) htmlcmd
	$(MAKE) mancmd

$(BIN)/$(PGM)$(EXE):  $(OBJ) $(DEPLIBS)
	$(CXX) $(LDFLAGS) -o $@ $(OBJ) $(LIBS)
