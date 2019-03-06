#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS Treatments class.
 *
 * Copyright (C) 2018 by the authors.
 *
 * Authors: Anna Petrasova <akratoc gmail com>
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

#include "raster.hpp"
#include "treatments.hpp"


using namespace pops;

int main()
{
    Treatments<Raster<int>, Raster<double>> treatments;
    treatments.clear_all();
    Raster<double> tr1 = {{1, 0}, {0, 0}};
    Raster<double> tr2 = {{0, 1}, {0, 0}};
    Raster<double> tr3 = {{0, 0}, {1, 0}};
    Raster<int> susceptible = {{10, 6}, {14, 15}};
    Raster<int> infected = {{1, 2}, {1, 1}};
    treatments.add_treatment(2000, tr1);
    treatments.add_treatment(2001, tr2);
    treatments.add_treatment(2002, tr3);
    treatments.apply_treatment_host(2000, infected, susceptible);
    treatments.apply_treatment_infected(2001, infected);

    Raster<int> treated = {{0, 6}, {14, 15}};
    Raster<int> inf_treated = {{0, 0}, {1, 1}};
    if (susceptible == treated && infected == inf_treated)
        std::cout << "Treatment works" << std::endl;
    else
        std::cout << "Treatment does not work" << std::endl;

    treatments.clear_after_year(2001);
    return 0;
}

#endif  // POPS_TEST
