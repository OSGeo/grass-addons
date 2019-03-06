#ifdef POPS_TEST

/*
 * Test for PoPS Date class.
 *
 * Copyright (C) 2018 by the authors.
 *
 * Authors: Vaclav Petras <wenzeslaus gmail com>

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

#include "date.hpp"

#include <map>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <string>

using std::string;
using std::cout;
using std::cerr;
using std::endl;

using pops::Date;

void test_years_by_month()
{
    Date start(2018, 1, 1);
    Date end(2020, 12, 31);

    while (start < end) {
        cout << start << endl;
        if (start.is_last_month_of_year()) {
            cout << "End of year" << endl;
        }
        start.increased_by_month();
    }
}

int main()
{
    // Test of date computations for SOD model
    test_years_by_month();

    return 0;
}

#endif  // POPS_TEST
