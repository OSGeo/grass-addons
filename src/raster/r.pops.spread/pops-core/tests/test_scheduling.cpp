#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS Scheduling class.
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

#include <vector>
#include <tuple>

#include <pops/scheduling.hpp>
#include <pops/date.hpp>

using namespace pops;

int test_schedule_spread_month()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 1);
    std::vector<bool> vect1 = scheduling1.schedule_spread(Season(1, 12));
    if (scheduling1.get_num_steps() != 24) {
        std::cout << "Failed scheduling of monthly spread" << std::endl;
        scheduling1.debug_schedule(vect1);
        num_errors++;
    }

    Scheduler scheduling2(st, end, StepUnit::Month, 3);
    std::vector<bool> vect2 = scheduling2.schedule_spread(Season(1, 12));
    if (scheduling2.get_num_steps() != 8) {
        std::cout << "Failed scheduling of monthly spread" << std::endl;
        scheduling2.debug_schedule(vect2);
        num_errors++;
    }

    Scheduler scheduling3(st, end, StepUnit::Month, 5);
    std::vector<bool> vect3 = scheduling3.schedule_spread(Season(1, 12));
    if (scheduling3.get_num_steps() != 5) {
        std::cout << "Failed scheduling of monthly spread" << std::endl;
        scheduling3.debug_schedule(vect3);
        num_errors++;
    }

    Date st2(2020, 2, 1);
    Date end2(2021, 12, 18);

    Scheduler scheduling4(st2, end2, StepUnit::Month, 2);
    std::vector<bool> vect4 = scheduling4.schedule_spread(Season(1, 12));
    if (scheduling4.get_num_steps() != 12) {
        std::cout << "Failed scheduling of monthly spread" << std::endl;
        scheduling4.debug_schedule(vect4);
        num_errors++;
    }

    Scheduler scheduling5(st2, end2, StepUnit::Month, 2);
    std::vector<bool> vect5 = scheduling5.schedule_spread(Season(3, 9));
    if (scheduling5.get_num_steps() != 12) {
        std::cout << "Failed scheduling of monthly spread" << std::endl;
        scheduling5.debug_schedule(vect5);
        num_errors++;
    }

    return num_errors;
}

int test_schedule_spread_days()
{
    int num_errors = 0;

    Date st(2020, 4, 7);
    Date end(2020, 11, 15);

    Scheduler scheduling1(st, end, StepUnit::Day, 21);
    std::vector<bool> vect1 = scheduling1.schedule_spread(Season(1, 12));
    if (scheduling1.get_num_steps() != 11) {
        std::cout << "Failed scheduling of 21-day spread" << std::endl;
        scheduling1.debug_schedule(vect1);
        num_errors++;
    }

    Date st1(2020, 12, 2);
    Date end1(2021, 4, 15);

    Scheduler scheduling2(st1, end1, StepUnit::Day, 21);
    std::vector<bool> vect2 = scheduling2.schedule_spread(Season(1, 12));
    if (scheduling2.get_num_steps() != 6) {
        std::cout << "Failed scheduling of 21-day spread" << std::endl;
        scheduling2.debug_schedule(vect2);
        num_errors++;
    }

    Date st2(2020, 12, 14);

    Scheduler scheduling3(st2, end1, StepUnit::Day, 21);
    std::vector<bool> vect3 = scheduling3.schedule_spread(Season(1, 12));
    if (scheduling3.get_num_steps() != 6) {
        std::cout << "Failed scheduling of 21-day spread" << std::endl;
        scheduling3.debug_schedule(vect3);
        num_errors++;
    }

    Date st3(2020, 12, 24);

    Scheduler scheduling4(st3, end1, StepUnit::Day, 21);
    std::vector<bool> vect4 = scheduling4.schedule_spread(Season(1, 12));
    if (scheduling3.get_num_steps() != 6) {
        std::cout << "Failed scheduling of 21-day spread" << std::endl;
        scheduling4.debug_schedule(vect4);
        num_errors++;
    }
    return num_errors;
}

int test_schedule_action_yearly()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 2);
    std::vector<bool> vect_action1 = scheduling1.schedule_action_yearly(4, 5);
    if (!(vect_action1[1] && vect_action1[7])) {
        scheduling1.debug_schedule(vect_action1);
        std::cout << "Failed scheduling of yearly action" << std::endl;
        num_errors++;
    }

    return num_errors;
}

int test_schedule_action_end_of_year()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 2);
    std::vector<bool> vect1 = scheduling1.schedule_spread(Season(1, 12));
    std::vector<bool> vect_action1 = scheduling1.schedule_action_end_of_year();
    if (scheduling1.get_num_steps() != 12) {
        std::cout << "Failed scheduling of end of year action" << std::endl;
        scheduling1.debug_schedule(vect_action1);
        num_errors++;
    }

    Date st1(2020, 1, 1);
    Date end1(2022, 11, 15);

    Scheduler scheduling2(st1, end1, StepUnit::Month, 2);
    std::vector<bool> vect2 = scheduling2.schedule_spread(Season(2, 8));
    std::vector<bool> vect_action2 = scheduling2.schedule_action_end_of_year();
    if (scheduling2.get_num_steps() != 18) {
        std::cout << "Failed scheduling of end of year action" << std::endl;
        scheduling2.debug_schedule(vect_action2);
        num_errors++;
    }

    return num_errors;
}

int test_schedule_action_nsteps()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 2);
    std::vector<bool> vect1 = scheduling1.schedule_spread(Season(1, 12));
    std::vector<bool> vect_action1 = scheduling1.schedule_action_nsteps(2);
    if (scheduling1.get_num_steps() != 12) {
        std::cout << "Failed scheduling of n-steps action" << std::endl;
        scheduling1.debug_schedule(vect_action1);
        num_errors++;
    }

    Scheduler scheduling2(st, end, StepUnit::Day, 15);
    std::vector<bool> vect2 = scheduling2.schedule_spread(Season(2, 10));
    std::vector<bool> vect_action2 = scheduling2.schedule_action_nsteps(2);
    if (scheduling2.get_num_steps() != 48) {
        std::cout << "Failed scheduling of n-steps action" << std::endl;
        scheduling2.debug_schedule(vect_action2);
        num_errors++;
    }

    return num_errors;
}

int test_schedule_action_monthly()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Day, 7);
    std::vector<bool> schedule = scheduling1.schedule_action_monthly();
    if (!(schedule[4] && schedule[8])) {
        std::cout << "Failed scheduling of monthly action" << std::endl;
        scheduling1.debug_schedule(schedule);
        num_errors++;
    }

    return num_errors;
}
int test_schedule_action_date()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 2);
    unsigned n = scheduling1.schedule_action_date(Date(2020, 3, 3));
    if (n != 1) {
        std::cout << "Failed scheduling of date action" << std::endl;
        scheduling1.debug_schedule(n);
        num_errors++;
    }

    return num_errors;
}

int test_schedule_end_of_simulation()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2020, 3, 3);

    Scheduler scheduling1(st, end, StepUnit::Week, 1);
    std::vector<bool> schedule =
        scheduling1.schedule_action_end_of_simulation();
    if (!(get_number_of_scheduled_actions(schedule) == 1 &&
          schedule[scheduling1.get_num_steps() - 1])) {
        std::cout << "Failed scheduling of end of simulation" << std::endl;
        scheduling1.debug_schedule(schedule);
        num_errors++;
    }

    return num_errors;
}

int test_simulation_step_to_action_step()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 1);
    std::vector<bool> vect_action1 = scheduling1.schedule_action_yearly(4, 5);
    unsigned i1 = simulation_step_to_action_step(vect_action1, 3);
    unsigned i2 = simulation_step_to_action_step(vect_action1, 15);
    if (!(i1 == 0 && i2 == 1)) {
        std::cout << "Failed simulation_step_to_action_step" << std::endl;
        num_errors++;
    }

    return num_errors;
}

int test_get_number_of_scheduled_actions()
{
    int num_errors = 0;

    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling1(st, end, StepUnit::Month, 1);
    std::vector<bool> vect_action1 = scheduling1.schedule_action_yearly(4, 5);
    unsigned n = get_number_of_scheduled_actions(vect_action1);
    if (n != 2) {
        std::cout << "Failed get_number_of_scheduled_actions" << std::endl;
        num_errors++;
    }

    return num_errors;
}

int test_unit_enum_from_string()
{
    int num_errors = 0;
    if (step_unit_enum_from_string("day") != StepUnit::Day)
        num_errors++;
    if (step_unit_enum_from_string("week") != StepUnit::Week)
        num_errors++;
    if (step_unit_enum_from_string("month") != StepUnit::Month)
        num_errors++;
    try {
        step_unit_enum_from_string("invalid_input");
        num_errors++;
    }
    catch (std::invalid_argument &) {
        // OK
    }
    catch (...) {
        num_errors++;
    }
    return num_errors;
}

int test_schedule_from_string()
{
    int num_errors = 0;
    Date st(2020, 1, 1);
    Date end(2020, 1, 28);

    Scheduler scheduling(st, end, StepUnit::Week, 1);
    std::vector<bool> out = schedule_from_string(scheduling, "week");
    if (get_number_of_scheduled_actions(out) != 4)
        num_errors++;
    out = schedule_from_string(scheduling, "every_n_steps", 2);
    if (get_number_of_scheduled_actions(out) != 2)
        num_errors++;
    try {
        out = schedule_from_string(scheduling, "day");
        num_errors++;
    }
    catch (std::invalid_argument &) {
        // OK
    }

    Scheduler scheduling2(st, end, StepUnit::Day, 1);
    out = schedule_from_string(scheduling2, "week");
    if (get_number_of_scheduled_actions(out) != 4)
        num_errors++;
    out = schedule_from_string(scheduling2, "day");
    if (get_number_of_scheduled_actions(out) != 28)
        num_errors++;
    out = schedule_from_string(scheduling2, "every_n_steps", 7);
    if (get_number_of_scheduled_actions(out) != 4)
        num_errors++;
    out = schedule_from_string(scheduling2, "final_step");
    if (get_number_of_scheduled_actions(out) != 1)
        num_errors++;

    Scheduler scheduling3(st, end, StepUnit::Week, 2);
    try {
        out = schedule_from_string(scheduling3, "week");
        num_errors++;
    }
    catch (std::invalid_argument &) {
        // OK
    }
    out = schedule_from_string(scheduling3, "every_n_steps", 2);
    if (get_number_of_scheduled_actions(out) != 1)
        num_errors++;
    out = schedule_from_string(scheduling3, "month");
    if (get_number_of_scheduled_actions(out) != 0)
        num_errors++;

    out = schedule_from_string(scheduling3, "", 0);
    if (get_number_of_scheduled_actions(out) != 0)
        num_errors++;
    return num_errors;
}

int test_get_step_length()
{
    int num_errors = 0;
    Date st(2020, 1, 1);
    Date end(2021, 12, 31);

    Scheduler scheduling(st, end, StepUnit::Month, 2);
    unsigned n;
    StepUnit unit;
    std::tie(n, unit) = scheduling.get_step_length();
    if (unit != StepUnit::Month || n != 2)
        num_errors++;

    return num_errors;
}

int main()
{
    int num_errors = 0;

    num_errors += test_schedule_spread_month();
    num_errors += test_schedule_spread_days();
    num_errors += test_schedule_action_yearly();
    num_errors += test_schedule_action_end_of_year();
    num_errors += test_schedule_action_nsteps();
    num_errors += test_schedule_action_date();
    num_errors += test_schedule_end_of_simulation();
    num_errors += test_schedule_action_monthly();
    num_errors += test_simulation_step_to_action_step();
    num_errors += test_get_number_of_scheduled_actions();
    num_errors += test_unit_enum_from_string();
    num_errors += test_get_step_length();
    num_errors += test_schedule_from_string();

    std::cout << "Test scheduling number of errors: " << num_errors
              << std::endl;
    return num_errors;
}

#endif // POPS_TEST
