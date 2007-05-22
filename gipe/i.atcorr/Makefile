MODULE_TOPDIR = ../..

PGM = i.atcorr

include $(MODULE_TOPDIR)/include/Make/Module.make

SOURCES = AerosolConcentration.cpp Transform.cpp Iwave.cpp Interp.cpp GeomCond.cpp gauss.cpp computations.cpp AtmosModel.cpp Altitude.cpp AerosolModel.cpp Abstra.cpp main.cpp Output.cpp common.cpp 6s.cpp

HEADERS = 6s.h common.h Output.h Abstra.h AerosolModel.h Altitude.h AtmosModel.h Gauss.h GeomCond.h Interp.h Iwave.h Transform.h AerosolConcentration.h

INCLUDE_GIS = $(INST_DIR)/include
LIBRARY_GIS = $(INST_DIR)/lib

OBJARCH=OBJ.$(ARCH)

$(OBJARCH)/%.o:%.cpp
	$(CXX) -c $< -o $@ -I$(INCLUDE_GIS) -L$(LIBRARY_GIS)

WARNING_FLAGS   = -Wformat  -Wparentheses  -Wpointer-arith -Wno-conversion \
  -Wimplicit-int -Wimplicit-function-declaration -Wreturn-type	\
  -Wcomment  -Wno-sign-compare


default: $(BIN)/$(PGM) $(BIN)/$(PGM) htmlcmd

$(BIN)/$(PGM): $(SOURCES)
	$(CXX) $(LDFLAGS) -o $@ $(GISLIB) $(SOURCES) -I $(INCLUDE_GIS) -L $(LIBRARY_GIS)

