CXXFLAGS := $(CXXFLAGS) -std=c++11 -pedantic -Wall -Wextra
COMMON_DEFINES := -D POPS_TEST

all: test_date test_raster test_simulation test_treatments

test_date: test_date.cpp date.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_date.cpp -o test_date

test_raster: test_raster.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_raster.cpp -o test_raster

test_simulation: test_simulation.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_simulation.cpp -o test_simulation

test_treatments: test_treatments.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_treatments.cpp -o test_treatments
test:
	./test_date
	./test_raster
	./test_simulation
	./test_treatments

doc:
	doxygen

clean:
	rm -f test_date
	rm -f test_raster
	rm -f test_simulation
	rm -f test_treatments
