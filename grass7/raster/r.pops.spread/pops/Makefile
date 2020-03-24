CXXFLAGS := $(CXXFLAGS) -std=c++11 -pedantic -Wall -Wextra
COMMON_DEFINES := -D POPS_TEST

all: test_date test_raster test_simulation test_treatments test_spread_rate test_statistics test_scheduling

test_date: test_date.cpp date.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_date.cpp -o test_date

test_raster: test_raster.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_raster.cpp -o test_raster

test_simulation: test_simulation.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_simulation.cpp -o test_simulation

test_treatments: test_treatments.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_treatments.cpp -o test_treatments

test_spread_rate: test_spread_rate.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_spread_rate.cpp -o test_spread_rate

test_statistics: test_statistics.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_statistics.cpp -o test_statistics

test_scheduling: test_scheduling.cpp *.hpp
	g++ $(CXXFLAGS) $(COMMON_DEFINES) test_scheduling.cpp -o test_scheduling
test:
	./test_date
	./test_raster
	./test_simulation
	./test_treatments
	./test_spread_rate
	./test_statistics
	./test_scheduling

doc:
	doxygen

clean:
	rm -f test_date
	rm -f test_raster
	rm -f test_simulation
	rm -f test_treatments
	rm -f test_spread_rate
	rm -f test_statistics
	rm -f test_scheduling
