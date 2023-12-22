#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS Simulation class.
 *
 * Copyright (C) 2018 by the authors.
 *
 * Authors: Vaclav Petras <wenzeslaus gmail com>
 *          Chris Jones <cmjone25 gmail com>
 *
 * This file is part of PoPS.

 * PoPS is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.

 * PoPS is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with PoPS. If not, see <https://www.gnu.org/licenses/>.
 */

#include <pops/raster.hpp>
#include <pops/simulation.hpp>

#include <map>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <string>

using std::cerr;
using std::cout;
using std::endl;
using std::string;

using namespace pops;

int main(int argc, char *argv[])
{
    Raster<int> infected = {{5, 0}, {0, 0}};
    Raster<int> mortality_tracker = {{{3, 0}, {0, 0}}, {{0, 0}, {0, 0}}};
    Raster<int> mortality = {{0, 0}, {0, 0}};
    int ew_res = 30;
    int ns_res = 30;
    double mortality_rate = 0.50;
    int current_year = 2018;
    int first_mortality_year = 2018;
    Simulation<Raster<int>, Raster<double>> simulation(42, infected, ew_res,
                                                       ns_res);
    simulation.mortality(infected, mortality_rate, current_year,
                         first_mortality_year, mortality,
                         mortality_tracker_vector) cout
        << mortality << endl;
    return 0;
}

#endif // POPS_TEST
