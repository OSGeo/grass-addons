/*
 * Tests for the PoPS Config class.
 *
 * Copyright (C) 2020 by the authors.
 *
 * Authors: Vaclav Petras <wenzeslaus gmail com>
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

#ifndef POPS_CONFIG_HPP
#define POPS_CONFIG_HPP

#include "scheduling.hpp"

#include <vector>

namespace pops {

class Config {
public:
    // Seed
    int random_seed{0};
    // Size
    int rows{0};
    int cols{0};
    double ew_res{0};
    double ns_res{0};
    // Reduced stochasticity
    bool generate_stochasticity{true};
    bool establishment_stochasticity{true};
    bool movement_stochasticity{true};
    bool deterministic{false};
    double establishment_probability{0};
    // Temperature
    bool use_lethal_temperature{false};
    double lethal_temperature{-273.15}; // 0 K
    int lethal_temperature_month{0};
    bool weather{false};
    double reproductive_rate{0};
    // SI/SEI
    std::string model_type;
    int latency_period_steps;
    // Kernels
    std::string natural_kernel_type;
    double natural_scale;
    std::string natural_direction;
    double natural_kappa;
    bool use_anthropogenic_kernel{false};
    double percent_natural_dispersal;
    std::string anthro_kernel_type;
    double anthro_scale;
    std::string anthro_direction;
    double anthro_kappa;
    // Treatments
    bool use_treatments{false};
    // Mortality
    bool use_mortality{false};
    double mortality_rate{0};
    int first_mortality_year{0}; // TODO: document that it starts at 1, not 0
    // Quarantine
    bool use_quarantine{false};
    std::string quarantine_frequency;
    unsigned quarantine_frequency_n;
    // Movements
    bool use_movements{false};
    std::vector<unsigned> movement_schedule;
    double dispersal_percentage{0.99};
    std::string output_frequency;
    unsigned output_frequency_n;
    bool use_spreadrates{true};
    std::string spreadrate_frequency;
    unsigned spreadrate_frequency_n;

    void create_schedules()
    {
        scheduler_ =
            Scheduler(date_start_, date_end_, step_unit_, step_num_units_);
        spread_schedule_ = scheduler_.schedule_spread(
            Season(season_start_month_, season_end_month_));
        output_schedule_ = schedule_from_string(scheduler_, output_frequency,
                                                output_frequency_n);
        mortality_schedule_ = scheduler_.schedule_action_end_of_year();
        if (use_lethal_temperature)
            lethal_schedule_ =
                scheduler_.schedule_action_yearly(lethal_temperature_month, 1);
        if (use_spreadrates)
            spread_rate_schedule_ = schedule_from_string(
                scheduler_, spreadrate_frequency, spreadrate_frequency_n);
        if (use_quarantine)
            quarantine_schedule_ = schedule_from_string(
                scheduler_, quarantine_frequency, quarantine_frequency_n);
        schedules_created_ = true;
    }

    const Scheduler &scheduler() const
    {
        if (!schedules_created_)
            throw std::logic_error(
                "Schedules were not created before calling scheduler()");
        return scheduler_;
    }

    const std::vector<bool> &spread_schedule() const
    {
        if (!schedules_created_)
            throw std::logic_error(
                "Schedules were not created before calling spread_schedule()");
        return spread_schedule_;
    }

    const std::vector<bool> &mortality_schedule() const
    {
        if (!schedules_created_)
            throw std::logic_error("Schedules were not created before calling "
                                   "mortality_schedule()");
        return mortality_schedule_;
    }

    const std::vector<bool> &lethal_schedule() const
    {
        if (!use_lethal_temperature)
            throw std::logic_error("lethal_schedule() not available when "
                                   "use_lethal_temperature is false");
        if (!schedules_created_)
            throw std::logic_error(
                "Schedules were not created before calling lethal_schedule()");
        return lethal_schedule_;
    }

    const std::vector<bool> &spread_rate_schedule() const
    {
        if (!use_spreadrates)
            throw std::logic_error("spread_rate_schedule() not available when "
                                   "use_spreadrates is false");
        if (!schedules_created_)
            throw std::logic_error("Schedules were not created before calling "
                                   "spread_rate_schedule()");
        return spread_rate_schedule_;
    }

    const std::vector<bool> &quarantine_schedule() const
    {
        if (!use_quarantine)
            throw std::logic_error("quarantine_schedule() not available when "
                                   "use_quarantine is false");
        if (!schedules_created_)
            throw std::logic_error("Schedules were not created before calling "
                                   "quarantine_schedule()");
        return quarantine_schedule_;
    }

    const std::vector<bool> &output_schedule() const
    {
        if (!schedules_created_)
            throw std::logic_error(
                "Schedules were not created before calling output_schedule()");
        return output_schedule_;
    }

    unsigned num_mortality_years()
    {
        if (!schedules_created_)
            throw std::logic_error("Schedules were not created before calling "
                                   "num_mortality_years()");
        return get_number_of_scheduled_actions(mortality_schedule_);
    }

    unsigned num_lethal()
    {
        if (!use_lethal_temperature)
            throw std::logic_error("num_lethal() not available when "
                                   "use_lethal_temperature is false");
        if (!schedules_created_)
            throw std::logic_error(
                "Schedules were not created before calling num_lethal()");
        return get_number_of_scheduled_actions(lethal_schedule_);
    }

    unsigned rate_num_steps()
    {
        if (!use_spreadrates)
            throw std::logic_error(
                "rate_num_steps() not available when use_spreadrates is false");
        if (!schedules_created_)
            throw std::logic_error(
                "Schedules were not created before calling rate_num_steps()");
        return get_number_of_scheduled_actions(spread_rate_schedule_);
    }

    unsigned quarantine_num_steps()
    {
        if (!use_quarantine)
            throw std::logic_error("quarantine_num_steps() not available when "
                                   "use_quarantine is false");
        if (!schedules_created_)
            throw std::logic_error("Schedules were not created before calling "
                                   "quarantine_num_steps()");
        return get_number_of_scheduled_actions(quarantine_schedule_);
    }

    const Date &date_start() const { return date_start_; }

    template <typename... Args>
    void set_date_start(Args &&...args)
    {
        date_start_ = Date(std::forward<Args>(args)...);
    }

    const Date &date_end() const { return date_end_; }

    template <typename... Args>
    void set_date_end(Args &&...args)
    {
        date_end_ = Date(std::forward<Args>(args)...);
    }

    StepUnit step_unit() const { return step_unit_; }

    void set_step_unit(StepUnit step_unit) { step_unit_ = step_unit; }

    void set_step_unit(const std::string &text)
    {
        step_unit_ = step_unit_enum_from_string(text);
    }

    unsigned step_num_units() const { return step_num_units_; }

    void set_step_num_units(unsigned step_num_units)
    {
        step_num_units_ = step_num_units;
    }

    // TODO: move to Season?
    void set_season_start_end_month(int start, int end)
    {
        season_start_month_ = start;
        season_end_month_ = end;
    }

    void set_season_start_end_month(const std::string &start,
                                    const std::string &end)
    {
        season_start_month_ = std::stoi(start);
        season_end_month_ = std::stoi(end);
    }

private:
    Date date_start_{"0-01-01"};
    Date date_end_{"0-01-02"};

    int season_start_month_{1};
    int season_end_month_{12};

    StepUnit step_unit_{StepUnit::Day};
    unsigned step_num_units_{1};

    Scheduler scheduler_{date_start_, date_end_, step_unit_, step_num_units_};
    bool schedules_created_{false};

    std::vector<bool> spread_schedule_;
    std::vector<bool> output_schedule_;
    std::vector<bool> mortality_schedule_;
    std::vector<bool> lethal_schedule_;
    std::vector<bool> spread_rate_schedule_;
    std::vector<bool> quarantine_schedule_;
};

} // namespace pops

#endif // POPS_CONFIG_HPP
