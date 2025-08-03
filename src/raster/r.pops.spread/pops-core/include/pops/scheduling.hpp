/*
 * PoPS model - scheduling simulation steps
 *
 * Copyright (C) 2015-2020 by the authors.
 *
 * Authors: Anna Petrasova
 *          Vaclav Petras
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_SCHEDULING_HPP
#define POPS_SCHEDULING_HPP

#include <iostream>
#include <vector>
#include <map>
#include <tuple>
#include <string>
#include <algorithm>

#include "date.hpp"

namespace pops {

/*! Representation and manipulation of a date for the simulation.
 *
 */

/*!
 * Simulation step representing an interval.
 */
class Step {
public:
    Step(Date start_date, Date end_date)
        : start_date_(start_date), end_date_(end_date)
    {
    }
    inline Date start_date() const { return start_date_; }
    inline Date end_date() const { return end_date_; }
    inline friend std::ostream &operator<<(std::ostream &os, const Step &step);

private:
    Date start_date_;
    Date end_date_;
};
std::ostream &operator<<(std::ostream &os, const Step &step)
{
    os << step.start_date_ << " - " << step.end_date_;
    return os;
}

/**
 * @brief Enum for step unit
 */
enum class StepUnit { Day, Week, Month };

/**
 * @brief Get step enum from string

 * Throws an std::invalid_argument exception if the value
 * is not supported.
 */
inline StepUnit step_unit_enum_from_string(const std::string &text)
{
    std::map<std::string, StepUnit> mapping{{"day", StepUnit::Day},
                                            {"week", StepUnit::Week},
                                            {"month", StepUnit::Month}};
    try {
        return mapping.at(text);
    }
    catch (const std::out_of_range &) {
        throw std::invalid_argument("step_unit_enum_from_string:"
                                    " Invalid value '" +
                                    text + "' provided");
    }
}

class Scheduler {
public:
    /**
     * Scheduler creates a vector of simulation steps
     * based on start, end date, unit and number of units.
     * The steps can be e.g. 1 day, 3 months, 2 weeks.
     * Step is scheduled if start date of an interval is
     * within [start, end] even if end date of the step is outside.
     * That means the entire interval is contained in the simulation steps
     * even when only part of it was requested.
     *
     * @param start simulation start date
     * @param end simulation end date
     * @param simulation_unit simulation unit
     * @param simulation_num_units number of days/weeks/months in a simulation
     * step
     */
    Scheduler(const Date &start, const Date &end, StepUnit simulation_unit,
              unsigned simulation_num_units)
        : start_(start), end_(end), simulation_unit_(simulation_unit),
          simulation_num_units_(simulation_num_units)
    {
        if (start >= end)
            throw std::invalid_argument("Start date must be before end date");
        if (simulation_num_units <= 0)
            throw std::invalid_argument(
                "Number of simulation units must be higher than zero");
        Date d(start);
        increase_date(d);
        if (d > end)
            throw std::invalid_argument(
                "There must be at least one step between start and end date");
        if (simulation_unit == StepUnit::Month && start.day() != 1)
            throw std::invalid_argument("If step unit is month, start date "
                                        "must start the first day of a "
                                        "month");

        Date date(start_);
        unsigned step = 0;
        while (date <= end_) {
            Date start(date);
            increase_date(date);
            Date end(date);
            end.subtract_day();
            steps.push_back(Step(start, end));
            step++;
        }
        num_steps = step;
    }

    /**
     * @brief Get number of simulation steps
     */
    unsigned get_num_steps() const { return num_steps; }

    /**
     * @brief Get step based on index
     */
    Step get_step(unsigned index) const { return steps.at(index); }

    /**
     * @brief Get length of simulation step as number of units and unit type
     */
    std::tuple<unsigned, StepUnit> get_step_length() const
    {
        return std::make_tuple(simulation_num_units_, simulation_unit_);
    }

    /**
     * @brief Schedule spread
     * @param season seasonality information
     * @return vector of bools, true if spread should happen that step
     */
    std::vector<bool> schedule_spread(const Season &season) const
    {
        std::vector<bool> schedule;
        schedule.reserve(num_steps);
        for (Step step : steps) {
            if (season.month_in_season(step.start_date().month()) ||
                season.month_in_season(step.end_date().month()))
                schedule.push_back(true);
            else
                schedule.push_back(false);
        }
        return schedule;
    }

    /**
     * @brief Schedule an action at certain date each year,
     *        e.g. lethality.
     *
     * This doesn't handle cases where there is change in year within interval,
     * but that doesn't happen with current implementation
     *
     * @param month month
     * @param day day
     * @return vector of bools, true if action should happen that step
     */
    std::vector<bool> schedule_action_yearly(int month, int day) const
    {
        std::vector<bool> schedule;
        schedule.reserve(num_steps);
        for (Step step : steps) {
            Date st = step.start_date();
            Date end = step.end_date();
            Date test(st.year(), month, day);
            if ((test >= st && test <= end))
                schedule.push_back(true);
            else
                schedule.push_back(false);
        }
        return schedule;
    }

    /**
     * @brief Schedule an action at the end of each year,
     *        e.g. mortality.
     * @return vector of bools, true if action should happen that step
     */
    std::vector<bool> schedule_action_end_of_year() const
    {
        std::vector<bool> schedule;
        schedule.reserve(num_steps);
        for (Step step : steps) {
            if (step.end_date().is_last_day_of_year())
                schedule.push_back(true);
            else
                schedule.push_back(false);
        }
        return schedule;
    }

    /**
     * @brief Schedule an action at the end of simulation.
     *
     * @return vector of bools, true if action should happen that step
     */
    std::vector<bool> schedule_action_end_of_simulation() const
    {
        std::vector<bool> schedule(num_steps, false);
        if (num_steps > 0)
            schedule[num_steps - 1] = true;
        return schedule;
    }

    /**
     * @brief Schedule action every N simulation steps,
     *
     * Useful for e.g. export. If simulation step is 2 months
     * and n_steps = 2, actions is scheduled every 4 months.
     * @param n_steps schedule every N steps
     * @return vector of bools, true if action should happen that step
     */
    std::vector<bool> schedule_action_nsteps(unsigned n_steps) const
    {
        std::vector<bool> schedule;
        schedule.reserve(num_steps);
        for (unsigned i = 0; i < num_steps; i++) {
            if ((i + 1) % n_steps == 0)
                schedule.push_back(true);
            else
                schedule.push_back(false);
        }
        return schedule;
    }

    /**
     * @brief Schedule action at the end of each month.
     *
     * More precisely, whenever end of the month is within the step interval.
     *
     * @return vector of bools, true if action should happen that step
     */
    std::vector<bool> schedule_action_monthly() const
    {
        std::vector<bool> schedule;
        schedule.reserve(num_steps);
        for (Step step : steps) {
            Date st = step.start_date();
            Date end = step.end_date();
            if (st.month() != end.month() || end.is_last_day_of_month())
                schedule.push_back(true);
            else
                schedule.push_back(false);
        }
        return schedule;
    }

    /**
     * @brief Schedule action at a specific date (not repeated action).
     *
     * Should be used within Treatments class.
     *
     * @param date date to schedule action
     * @return index of step
     */
    unsigned schedule_action_date(const Date &date) const
    {
        for (unsigned i = 0; i < num_steps; i++) {
            if (date >= steps[i].start_date() && date <= steps[i].end_date())
                return i;
        }
        throw std::invalid_argument("Date is outside of schedule");
    }
    /**
     * @brief Prints schedule for debugging purposes.
     * @param vector of bools to print along the steps
     */
    void debug_schedule(std::vector<bool> &schedule) const
    {
        for (unsigned i = 0; i < num_steps; i++)
            std::cout << steps[i] << ": " << (schedule.at(i) ? "true" : "false")
                      << std::endl;
    }
    void debug_schedule(unsigned n) const
    {
        for (unsigned i = 0; i < num_steps; i++)
            std::cout << steps[i] << ": " << (n == i ? "true" : "false")
                      << std::endl;
    }
    void debug_schedule() const
    {
        for (unsigned i = 0; i < num_steps; i++)
            std::cout << steps[i] << std::endl;
    }

private:
    Date start_;
    Date end_;
    StepUnit simulation_unit_;
    unsigned simulation_num_units_;
    std::vector<Step> steps;
    unsigned num_steps;

    /**
     * @brief Increse date by simulation step
     * @param date date
     */
    void increase_date(Date &date)
    {
        if (simulation_unit_ == StepUnit::Day) {
            date.increased_by_days(simulation_num_units_);
        }
        else if (simulation_unit_ == StepUnit::Week) {
            for (unsigned i = 0; i < simulation_num_units_; i++) {
                date.increased_by_week();
            }
        }
        else if (simulation_unit_ == StepUnit::Month) {
            for (unsigned i = 0; i < simulation_num_units_; i++) {
                date.increased_by_month();
            }
        }
    }
};

/**
 * Converts simulation step to step of actions.
 * This is useful for getting the right index of
 * lethal temperature file.
 *
 * schedule: [F, T, F, F, F, T, F]
 * step: 1 -> returns 0
 * step: 5 -> returns 1
 *
 * Result for input step any other then 1 and 5 in this case
 * returns valid number but has no particular meaning.
 */
unsigned
simulation_step_to_action_step(const std::vector<bool> &action_schedule,
                               unsigned step)
{
    std::vector<unsigned> indices(action_schedule.size());
    unsigned idx = 0;
    for (unsigned i = 0; i < action_schedule.size(); i++) {
        indices[i] = idx;
        if (action_schedule[i])
            ++idx;
    }
    return indices.at(step);
}

/**
 * Returns how many actions are scheduled.
 *
 * action_schedule: [F, T, F, F, F, T, F] -> 2
 */
unsigned
get_number_of_scheduled_actions(const std::vector<bool> &action_schedule)
{
    return std::count(action_schedule.begin(), action_schedule.end(), true);
}

/**
 * @brief Get output (export) schedule based on
 * frequency string ("year", "month", "week", "day", "every_n_steps",
 * "final_step"). If frequency is "every_n_steps", then output is scheduled
 * every n steps of the simulation.
 *
 * Throws an std::invalid_argument exception if the value
 * is not supported or the output frequency is not compatible with
 * simulation step (e.g., frequency is weekly, but simulation runs every 2
 * weeks). If frequency is empty string, empty output schedule is returned.
 */
inline std::vector<bool> schedule_from_string(const Scheduler &scheduler,
                                              const std::string &frequency,
                                              unsigned n = 0)
{
    StepUnit sim_unit;
    unsigned sim_n;
    std::invalid_argument exception(
        "Output frequency and simulation step are incompatible");
    std::tie(sim_n, sim_unit) = scheduler.get_step_length();
    if (!frequency.empty()) {
        if (frequency == "final_step")
            return scheduler.schedule_action_end_of_simulation();
        else if (frequency == "year" || frequency == "yearly")
            return scheduler.schedule_action_end_of_year();
        else if (frequency == "month" || frequency == "monthly")
            return scheduler.schedule_action_monthly();
        else if (frequency == "week" || frequency == "weekly") {
            if (sim_unit == StepUnit::Day) {
                if (sim_n == 1)
                    return scheduler.schedule_action_nsteps(7);
                else if (sim_n == 7)
                    return scheduler.schedule_action_nsteps(1);
                else
                    throw exception;
            }
            else if (sim_unit == StepUnit::Week) {
                if (sim_n == 1)
                    return scheduler.schedule_action_nsteps(1);
                else
                    throw exception;
            }
            throw exception;
        }
        else if (frequency == "day" || frequency == "daily") {
            if (sim_unit == StepUnit::Day && sim_n == 1)
                return scheduler.schedule_action_nsteps(1);
            else
                throw exception;
        }
        else if (frequency == "every_n_steps" && n > 0)
            return scheduler.schedule_action_nsteps(n);
        else
            throw std::invalid_argument("Invalid value of output frequency");
    }
    else {
        std::vector<bool> v(scheduler.get_num_steps(), false);
        return v;
    }
}

} // namespace pops

#endif // POPS_SCHEDULING_HPP
