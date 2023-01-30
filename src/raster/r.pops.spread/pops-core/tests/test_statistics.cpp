#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS statistics class.
 *
 * Copyright (C) 2018-2019 by the authors.
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

#include <pops/raster.hpp>
#include <pops/statistics.hpp>

using namespace pops;

int test_sum()
{
    int err = 0;
    Raster<int> infected = {{0, 0, 0, 0, 25},
                            {1, 0, 0, 0, 0},
                            {0, 0, 1, 0, 0},
                            {0, 0, 5, 0, 0},
                            {0, 0, 0, 0, 0}};

    unsigned sum = sum_of_infected(infected);

    if (sum != 32) {
        std::cout << "sum fails" << std::endl;
        err++;
    }

    return err;
}

int test_area()
{
    int err = 0;
    Raster<int> infected = {{0, 0, 0, 0, 25},
                            {1, 0, 0, 0, 0},
                            {0, 0, 1, 0, 0},
                            {0, 0, 5, 0, 0},
                            {0, 0, 0, 0, 0}};

    double area = area_of_infected(infected, 0.5, 1);

    if (area != 2) {
        std::cout << "area fails" << std::endl;
        err++;
    }

    return err;
}

int main()
{
    int num_errors = 0;

    num_errors += test_sum();
    num_errors += test_area();
    std::cout << "Statistics number of errors: " << num_errors << std::endl;
    return num_errors;
}

#endif // POPS_TEST
