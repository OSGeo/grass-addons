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

#include <pops/date.hpp>

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

int test_last_day_of_step()
{
    int num_errors = 0;
    Date d1(2018, 1, 3);
    Date d2(2000, 2, 1);
    Date d3(2001, 2, 4);

    if (d1.get_last_day_of_month() != Date(2018, 1, 31)) {
        num_errors++;
        cout << d1 << endl;
    }
    if (d2.get_last_day_of_month() != Date(2000, 2, 29)) {
        num_errors++;
        cout << d2 << endl;
    }
    if (d3.get_last_day_of_month() != Date(2001, 2, 28)) {
        num_errors++;
        cout << d3 << endl;
    }

    Date d4(2019, 4, 4);
    Date d5(2019, 12, 17);
    Date d6(2019, 12, 18);
    if (d4.get_last_day_of_week() != Date(2019, 4, 10)) {
        num_errors++;
        cout << d4 << d4.get_last_day_of_week() << endl;
    }
    if (d5.get_last_day_of_week() != Date(2019, 12, 23)) {
        num_errors++;
        cout << d5 << d5.get_last_day_of_week() << endl;
    }
    if (d6.get_last_day_of_week() != Date(2019, 12, 31)) {
        num_errors++;
        cout << d6 << d6.get_last_day_of_week() << endl;
    }
    return num_errors;
}

int test_from_string()
{
    int num_errors = 0;
    Date d = Date("2020-02-01");
    if (d.year() != 2020 || d.month() != 2 || d.day() != 1) {
        num_errors++;
        cout << d << endl;
    }
    try {
        d = Date("2015-31-01");
    }
    catch (std::invalid_argument &) {
        // pass
    }
    try {
        d = Date("2016-04-31");
    }
    catch (std::invalid_argument &) {
        // pass
    }
    if (d.year() != 2020 || d.month() != 2 || d.day() != 1) {
        num_errors++;
        cout << d << endl;
    }
    return num_errors;
}

int test_add_days()
{
    int num_errors = 0;
    Date d = Date("2000-02-28");
    d.add_days(2);
    if (d.month() != 3 || d.day() != 1) {
        num_errors++;
        cout << d << endl;
    }
    d = Date("2001-12-31");
    d.add_days(366);
    if (d.year() != 2003 || d.month() != 1 || d.day() != 1) {
        num_errors++;
        cout << d << endl;
    }
    return num_errors;
}

int test_subtract_days()
{
    int num_errors = 0;
    Date d = Date("2000-03-01");
    d.subtract_days(2);
    if (d.month() != 2 || d.day() != 28) {
        num_errors++;
        cout << d << endl;
    }
    d = Date("2002-01-01");
    d.subtract_days(366);
    if (d.year() != 2000 || d.month() != 12 || d.day() != 31) {
        num_errors++;
        cout << d << endl;
    }
    return num_errors;
}

int main()
{
    int num_errors = 0;
    // Test of date computations for SOD model
    test_years_by_month();
    num_errors += test_last_day_of_step();
    num_errors += test_from_string();
    num_errors += test_add_days();
    num_errors += test_subtract_days();
    cout << "Test Date class: number of errors: " << num_errors << endl;

    return 0;
}

#endif // POPS_TEST
