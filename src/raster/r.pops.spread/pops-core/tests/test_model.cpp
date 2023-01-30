#ifdef POPS_TEST

/*
 * Tests for the PoPS Model class.
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

#include <pops/model.hpp>

using namespace pops;
using std::cout;

int test_with_reduced_stochasticity()
{
    Raster<int> infected = {{5, 0}, {0, 0}};
    Raster<int> susceptible = {{10, 20}, {14, 15}};
    Raster<int> total_hosts = susceptible;
    Raster<int> zeros(infected.rows(), infected.cols(), 0);

    Raster<int> expected_mortality_tracker = {{0, 10}, {0, 0}};
    auto expected_infected = expected_mortality_tracker + infected;

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;
    Config config;
    config.weather = false;
    config.reproductive_rate = 2;
    config.generate_stochasticity = false;
    config.establishment_stochasticity = false;
    // We want everything to establish.
    config.establishment_probability = 1;
    config.natural_kernel_type = "deterministic_neighbor";
    config.natural_direction = "E";
    config.use_anthropogenic_kernel = false;
    config.random_seed = 42;
    config.rows = infected.rows();
    config.cols = infected.cols();
    config.model_type = "SI";
    config.latency_period_steps = 0;
    config.use_lethal_temperature = false;
    config.use_quarantine = true;
    config.quarantine_frequency = "year";
    config.quarantine_frequency_n = 1;
    config.use_spreadrates = true;
    config.spreadrate_frequency = "year";
    config.spreadrate_frequency_n = 1;

    config.set_date_start(2020, 1, 1);
    config.set_date_end(2021, 12, 31);
    config.set_step_unit(StepUnit::Month);
    config.set_step_num_units(1);
    config.create_schedules();

    unsigned num_mortality_years = config.num_mortality_years();
    std::cerr << "num_mortality_years: " << num_mortality_years << "\n";
    std::vector<Raster<int>> mortality_tracker(
        num_mortality_years, Raster<int>(infected.rows(), infected.cols(), 0));

    //    int exposed_size = 0;
    //    if (config.latency_period_steps)
    //        exposed_size = config.latency_period_steps + 1;
    //    std::vector<Raster<int>> exposed(
    //                exposed_size,
    //                Raster<int>(infected.rows(), infected.cols(), 0));
    Raster<int> died(infected.rows(), infected.cols(), 0);
    std::vector<Raster<int>> empty_integer;
    std::vector<Raster<double>> empty_float;
    Treatments<Raster<int>, Raster<double>> treatments(config.scheduler());
    config.use_treatments = false;
    config.ew_res = 1;
    config.ns_res = 1;
    unsigned rate_num_steps =
        get_number_of_scheduled_actions(config.spread_rate_schedule());
    unsigned quarantine_num_steps =
        get_number_of_scheduled_actions(config.quarantine_schedule());
    SpreadRate<Raster<int>> spread_rate(infected, config.ew_res, config.ns_res,
                                        rate_num_steps);
    QuarantineEscape<Raster<int>> quarantine(
        zeros, config.ew_res, config.ns_res, quarantine_num_steps);

    auto expected_dispersers = config.reproductive_rate * infected;
    std::vector<std::vector<int>> movements = {
        {0, 0, 1, 1, 2}, {0, 1, 0, 0, 3}, {0, 1, 1, 0, 2}};

    int step = 0;

    Model<Raster<int>, Raster<double>, Raster<double>::IndexType> model(config);
    model.run_step(step++, infected, susceptible, total_hosts, dispersers,
                   empty_integer, mortality_tracker, died, empty_float,
                   empty_float[0], treatments, zeros, outside_dispersers,
                   spread_rate, quarantine, zeros, movements);
    if (dispersers != expected_dispersers) {
        cout << "reduced_stochasticity: dispersers (actual, expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    if (!outside_dispersers.empty()) {
        cout << "reduced_stochasticity: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "reduced_stochasticity: infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    if (mortality_tracker[0] != expected_mortality_tracker) {
        cout << "reduced_stochasticity: mortality tracker (actual, expected):\n"
             << mortality_tracker[0] << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    return 0;
}
int test_deterministic()
{
    Raster<int> infected = {{5, 0, 0}, {0, 5, 0}, {0, 0, 2}};
    Raster<int> susceptible = {{10, 20, 9}, {14, 15, 0}, {3, 0, 2}};
    Raster<int> total_hosts = susceptible;
    Raster<int> zeros(infected.rows(), infected.cols(), 0);

    Raster<int> expected_mortality_tracker = {
        {10, 0, 0}, {0, 10, 0}, {0, 0, 2}};
    Raster<int> expected_infected = {{15, 0, 0}, {0, 15, 0}, {0, 0, 4}};

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;

    Config config;
    config.weather = false;
    config.reproductive_rate = 2;
    config.generate_stochasticity = false;
    config.establishment_stochasticity = false;
    config.movement_stochasticity = false;
    std::vector<std::vector<int>> movements = {
        {0, 0, 1, 1, 2}, {0, 1, 0, 0, 3}, {0, 1, 1, 0, 2}};
    config.movement_schedule = {1, 1};

    // We want everything to establish.
    config.establishment_probability = 1;
    config.natural_kernel_type = "cauchy";
    config.natural_direction = "none";
    config.natural_scale = 0.9;
    config.anthro_scale = 0.9;
    config.dispersal_percentage = 0.9;
    config.natural_kappa = 0;
    config.anthro_kappa = 0;

    config.use_anthropogenic_kernel = false;
    config.random_seed = 42;
    config.rows = infected.rows();
    config.cols = infected.cols();
    config.model_type = "SI";
    config.latency_period_steps = 0;
    config.use_lethal_temperature = false;
    config.use_quarantine = false;
    config.use_spreadrates = true;
    config.spreadrate_frequency = "year";
    config.spreadrate_frequency_n = 1;

    config.set_date_start(2020, 1, 1);
    config.set_date_end(2021, 12, 31);
    config.set_step_unit(StepUnit::Month);
    config.set_step_num_units(1);
    config.create_schedules();

    config.deterministic = true;

    unsigned num_mortality_years = config.num_mortality_years();
    std::vector<Raster<int>> mortality_tracker(
        num_mortality_years, Raster<int>(infected.rows(), infected.cols(), 0));

    Raster<int> died(infected.rows(), infected.cols(), 0);
    std::vector<Raster<int>> empty_integer;
    std::vector<Raster<double>> empty_float;
    Treatments<Raster<int>, Raster<double>> treatments(config.scheduler());
    config.use_treatments = false;
    config.ew_res = 30;
    config.ns_res = 30;
    unsigned rate_num_steps =
        get_number_of_scheduled_actions(config.spread_rate_schedule());
    SpreadRate<Raster<int>> spread_rate(infected, config.ew_res, config.ns_res,
                                        rate_num_steps);
    QuarantineEscape<Raster<int>> quarantine(zeros, config.ew_res,
                                             config.ns_res, 0);

    auto expected_dispersers = config.reproductive_rate * infected;

    int step = 0;

    Model<Raster<int>, Raster<double>, Raster<double>::IndexType> model(config);
    model.run_step(step++, infected, susceptible, total_hosts, dispersers,
                   empty_integer, mortality_tracker, died, empty_float,
                   empty_float[0], treatments, zeros, outside_dispersers,
                   spread_rate, quarantine, zeros, movements);
    if (dispersers != expected_dispersers) {
        cout << "deterministic: dispersers (actual, expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    if (!outside_dispersers.empty()) {
        cout << "deterministic: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "deterministic: infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    if (mortality_tracker[0] != expected_mortality_tracker) {
        cout << "deterministic: mortality tracker (actual, expected):\n"
             << mortality_tracker[0] << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    return 0;
}
int test_deterministic_exponential()
{
    Raster<int> infected = {{5, 0, 0}, {0, 5, 0}, {0, 0, 2}};
    Raster<int> susceptible = {{10, 20, 9}, {14, 15, 0}, {3, 0, 2}};
    Raster<int> total_hosts = susceptible;
    Raster<int> zeros(infected.rows(), infected.cols(), 0);

    Raster<int> expected_mortality_tracker = {
        {10, 0, 0}, {0, 10, 0}, {0, 0, 2}};
    Raster<int> expected_infected = {{15, 0, 0}, {0, 15, 0}, {0, 0, 4}};

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;

    Config config;
    config.weather = false;
    config.reproductive_rate = 2;
    config.generate_stochasticity = false;
    config.establishment_stochasticity = false;
    config.movement_stochasticity = false;
    std::vector<std::vector<int>> movements = {
        {0, 0, 1, 1, 2}, {0, 1, 0, 0, 3}, {0, 1, 1, 0, 2}};
    config.movement_schedule = {1, 1};

    // We want everything to establish.
    config.establishment_probability = 1;
    config.natural_kernel_type = "exponential";
    config.natural_direction = "none";
    config.natural_scale = 1;
    config.anthro_scale = 1;
    config.natural_kappa = 0;
    config.anthro_kappa = 0;
    config.dispersal_percentage = 0.99;
    config.use_anthropogenic_kernel = false;
    config.random_seed = 42;
    config.rows = infected.rows();
    config.cols = infected.cols();
    config.model_type = "SI";
    config.latency_period_steps = 0;
    config.use_lethal_temperature = false;
    config.use_quarantine = false;
    config.use_spreadrates = true;
    config.spreadrate_frequency = "year";
    config.spreadrate_frequency_n = 1;

    config.set_date_start(2020, 1, 1);
    config.set_date_end(2021, 12, 31);
    config.set_step_unit(StepUnit::Month);
    config.set_step_num_units(1);
    config.create_schedules();

    config.deterministic = true;

    unsigned num_mortality_years = config.num_mortality_years();
    std::vector<Raster<int>> mortality_tracker(
        num_mortality_years, Raster<int>(infected.rows(), infected.cols(), 0));

    Raster<int> died(infected.rows(), infected.cols(), 0);
    std::vector<Raster<int>> empty_integer;
    std::vector<Raster<double>> empty_float;
    Treatments<Raster<int>, Raster<double>> treatments(config.scheduler());
    config.use_treatments = false;
    config.ew_res = 30;
    config.ns_res = 30;
    unsigned rate_num_steps =
        get_number_of_scheduled_actions(config.spread_rate_schedule());
    SpreadRate<Raster<int>> spread_rate(infected, config.ew_res, config.ns_res,
                                        rate_num_steps);
    QuarantineEscape<Raster<int>> quarantine(zeros, config.ew_res,
                                             config.ns_res, 0);

    auto expected_dispersers = config.reproductive_rate * infected;

    int step = 0;

    Model<Raster<int>, Raster<double>, Raster<double>::IndexType> model(config);
    model.run_step(step++, infected, susceptible, total_hosts, dispersers,
                   empty_integer, mortality_tracker, died, empty_float,
                   empty_float[0], treatments, zeros, outside_dispersers,
                   spread_rate, quarantine, zeros, movements);
    if (dispersers != expected_dispersers) {
        cout << "deterministic exponential: dispersers (actual, expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    if (!outside_dispersers.empty()) {
        cout << "deterministic exponential: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "deterministic exponential: infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    if (mortality_tracker[0] != expected_mortality_tracker) {
        cout << "deterministic exponential: mortality tracker (actual, "
                "expected):\n"
             << mortality_tracker[0] << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    return 0;
}

int test_model_sei_deterministic()
{
    Raster<int> infected = {{5, 0, 0}, {0, 5, 0}, {0, 0, 2}};
    Raster<int> susceptible = {{95, 100, 100}, {100, 95, 100}, {100, 0, 98}};
    Raster<int> total_hosts = susceptible;
    Raster<int> zeros(infected.rows(), infected.cols(), 0);

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;

    Config config;
    config.reproductive_rate = 1;
    config.generate_stochasticity = false;
    config.establishment_stochasticity = false;
    config.movement_stochasticity = false;

    // We want everything to establish.
    config.establishment_probability = 1;
    config.natural_kernel_type = "cauchy";
    config.natural_direction = "none";
    config.natural_scale = 0.9;
    config.anthro_scale = 0.9;
    config.dispersal_percentage = 0.9;
    config.natural_kappa = 0;
    config.anthro_kappa = 0;

    config.use_anthropogenic_kernel = false;
    config.random_seed = 42;
    config.rows = infected.rows();
    config.cols = infected.cols();
    config.model_type = "SEI";
    config.latency_period_steps = 11;
    config.use_lethal_temperature = false;
    config.use_quarantine = false;
    config.use_spreadrates = true;
    config.spreadrate_frequency = "year";
    config.spreadrate_frequency_n = 1;

    config.set_date_start(2020, 1, 1);
    config.set_date_end(2020, 12, 31);
    config.set_step_unit(StepUnit::Month);
    config.set_step_num_units(1);
    config.create_schedules();

    config.deterministic = true;

    std::vector<std::vector<int>> movements;

    unsigned num_mortality_years = config.num_mortality_years();
    std::vector<Raster<int>> mortality_tracker(
        num_mortality_years, Raster<int>(infected.rows(), infected.cols(), 0));

    Raster<int> died(infected.rows(), infected.cols(), 0);
    int exposed_size = 0;
    if (config.latency_period_steps)
        exposed_size = config.latency_period_steps + 1;
    std::vector<Raster<int>> exposed(
        exposed_size, Raster<int>(infected.rows(), infected.cols(), 0));
    std::vector<Raster<double>> empty_float;
    Treatments<Raster<int>, Raster<double>> treatments(config.scheduler());
    config.use_treatments = false;
    config.ew_res = 30;
    config.ns_res = 30;
    unsigned rate_num_steps =
        get_number_of_scheduled_actions(config.spread_rate_schedule());
    SpreadRate<Raster<int>> spread_rate(infected, config.ew_res, config.ns_res,
                                        rate_num_steps);
    QuarantineEscape<Raster<int>> quarantine(zeros, config.ew_res,
                                             config.ns_res, 0);

    // There should be still the original number of infected when dispersers are
    // created.
    auto expected_dispersers = config.reproductive_rate * infected;
    // One E to I transition should happen.
    auto expected_infected = config.reproductive_rate * infected + infected;

    Model<Raster<int>, Raster<double>, Raster<double>::IndexType> model(config);
    for (unsigned int step = 0; step < config.scheduler().get_num_steps();
         ++step) {
        model.run_step(step, infected, susceptible, total_hosts, dispersers,
                       exposed, mortality_tracker, died, empty_float,
                       empty_float[0], treatments, zeros, outside_dispersers,
                       spread_rate, quarantine, zeros, movements);
    }
    if (dispersers != expected_dispersers) {
        cout << "sei_deterministic: dispersers (actual, expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    if (!outside_dispersers.empty()) {
        cout << "sei_deterministic: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "sei_deterministic: infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    return 0;
}

int test_model_sei_deterministic_with_treatments()
{
    // Raster<int> infected = {{7, 0, 0}, {0, 50, 0}, {0, 0, 200}};
    Raster<int> infected = {{5, 0, 0}, {0, 10, 0}, {0, 0, 2}};
    Raster<int> susceptible = {{95, 100, 100}, {100, 95, 100}, {100, 0, 98}};
    Raster<int> total_hosts = susceptible;
    Raster<int> zeros(infected.rows(), infected.cols(), 0);

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;

    Config config;
    config.reproductive_rate = 1;
    config.generate_stochasticity = false;
    config.establishment_stochasticity = false;
    config.movement_stochasticity = false;

    // We want everything to establish.
    config.establishment_probability = 1;
    config.natural_kernel_type = "cauchy";
    config.natural_direction = "none";
    config.natural_scale = 0.9;
    config.anthro_scale = 0.9;
    config.dispersal_percentage = 0.9;
    config.natural_kappa = 0;
    config.anthro_kappa = 0;

    config.use_anthropogenic_kernel = false;
    config.random_seed = 42;
    config.rows = infected.rows();
    config.cols = infected.cols();
    config.model_type = "SEI";
    config.latency_period_steps = 11;
    config.use_lethal_temperature = false;
    config.use_quarantine = false;
    config.use_spreadrates = true;
    config.spreadrate_frequency = "year";
    config.spreadrate_frequency_n = 1;

    config.set_date_start(2020, 1, 1);
    config.set_date_end(2020, 12, 31);
    config.set_step_unit(StepUnit::Month);
    config.set_step_num_units(1);
    config.create_schedules();

    config.deterministic = true;

    std::vector<std::vector<int>> movements;

    unsigned num_mortality_years = config.num_mortality_years();
    std::vector<Raster<int>> mortality_tracker(
        num_mortality_years, Raster<int>(infected.rows(), infected.cols(), 0));

    Raster<int> died(infected.rows(), infected.cols(), 0);
    int exposed_size = 0;
    if (config.latency_period_steps)
        exposed_size = config.latency_period_steps + 1;
    std::vector<Raster<int>> exposed(
        exposed_size, Raster<int>(infected.rows(), infected.cols(), 0));
    std::vector<Raster<double>> empty_float;
    Treatments<Raster<int>, Raster<double>> treatments(config.scheduler());
    Raster<double> simple_treatment = {{1, 0, 0}, {0, 0, 0}, {0, 0, 0}};
    treatments.add_treatment(simple_treatment, Date(2020, 1, 1), 0,
                             TreatmentApplication::AllInfectedInCell);
    Raster<double> pesticide_treatment = {{0, 0, 0}, {0, 0.5, 0}, {0, 0, 0}};
    treatments.add_treatment(pesticide_treatment, Date(2020, 1, 1), 365,
                             TreatmentApplication::Ratio);
    config.use_treatments = true;
    config.ew_res = 30;
    config.ns_res = 30;
    unsigned rate_num_steps =
        get_number_of_scheduled_actions(config.spread_rate_schedule());
    SpreadRate<Raster<int>> spread_rate(infected, config.ew_res, config.ns_res,
                                        rate_num_steps);
    QuarantineEscape<Raster<int>> quarantine(zeros, config.ew_res,
                                             config.ns_res, 0);

    // There should be still the original number of infected when dispersers are
    // created.
    auto expected_dispersers = config.reproductive_rate * infected;
    // One E to I transition should happen.
    auto expected_infected = config.reproductive_rate * infected + infected;
    // Apply treatment to expected results (assuming rate == 1)
    // (modifying int with double is not allowed in Raster, so we have to be
    // explicit) Remove infected
    for (int row = 0; row < expected_infected.rows(); ++row)
        for (int col = 0; col < expected_infected.rows(); ++col)
            expected_infected(row, col) *= !simple_treatment(row, col);
    // Reduced number of infected
    // (assuming 1 infection (E to I) step completed, i.e. 1 initial state + 1
    // step)
    for (int row = 0; row < expected_infected.rows(); ++row)
        for (int col = 0; col < expected_infected.rows(); ++col)
            if (pesticide_treatment(row, col) > 0)
                expected_infected(row, col) =
                    2 * pesticide_treatment(row, col) * infected(row, col);

    Model<Raster<int>, Raster<double>, Raster<double>::IndexType> model(config);
    for (unsigned int step = 0; step < config.scheduler().get_num_steps();
         ++step) {
        model.run_step(step, infected, susceptible, total_hosts, dispersers,
                       exposed, mortality_tracker, died, empty_float,
                       empty_float[0], treatments, zeros, outside_dispersers,
                       spread_rate, quarantine, zeros, movements);
    }
    if (!outside_dispersers.empty()) {
        cout << "sei_deterministic_with_treatments: There are "
                "outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "sei_deterministic_with_treatments: infected (actual, "
                "expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    return 0;
}

int main()
{
    int ret = 0;

    ret += test_with_reduced_stochasticity();
    ret += test_deterministic();
    ret += test_deterministic_exponential();
    ret += test_model_sei_deterministic();
    ret += test_model_sei_deterministic_with_treatments();
    std::cout << "Test model number of errors: " << ret << std::endl;

    return ret;
}

#endif // POPS_TEST
