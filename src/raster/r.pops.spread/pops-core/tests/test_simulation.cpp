#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS Simulation class.
 *
 * Copyright (C) 2018-2020 by the authors.
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

#include <pops/raster.hpp>
#include <pops/radial_kernel.hpp>
#include <pops/neighbor_kernel.hpp>
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

template <typename T>
void print_vector(const std::vector<T> &v)
{
    for (auto i : v) {
        cout << i;
    }
    cout << "\n";
}

int test_rotate_left_by_one(std::vector<int> a, std::vector<int> b)
{
    rotate_left_by_one(a);
    if (a != b) {
        cout << "Rotated vector not correct\n";
        print_vector(a);
        print_vector(b);
        return 1;
    }
    return 0;
}

int test_with_neighbor_kernel()
{
    Raster<int> infected = {{5, 0}, {0, 0}};
    Raster<int> mortality_tracker = {{0, 0}, {0, 0}};
    // Susceptible and total are set in a way that there won't be any
    // dilution effect and the disperser will always establish given the
    // selected random seed. Establishment probability is high and with
    // the given seed we don't get any random numbers in establishment
    // test higher than that. (The weather is disabled.)
    Raster<int> susceptible = {{10, 6}, {14, 15}};
    // add a lot of hosts, so that exposing or infecting them won't
    // chanage the susceptible/total ratio much
    susceptible += 100000;
    // we want to minimize the dilution effect
    Raster<int> total_hosts = susceptible;
    Raster<double> temperature = {{5, 0}, {0, 0}};
    Raster<double> weather_coefficient = {{0, 0}, {0, 0}};

    Raster<int> expected_mortality_tracker = {{0, 10}, {0, 0}};
    auto expected_infected = expected_mortality_tracker + infected;

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;
    bool weather = false;
    double reproductive_rate = 2;
    DeterministicNeighborDispersalKernel kernel(Direction::E);
    Simulation<Raster<int>, Raster<double>> simulation(42, infected.rows(),
                                                       infected.cols());
    dispersers = reproductive_rate * infected;
    // cout << dispersers;
    simulation.disperse(dispersers, susceptible, infected, mortality_tracker,
                        total_hosts, outside_dispersers, weather,
                        weather_coefficient, kernel);
    if (!outside_dispersers.empty()) {
        cout << "There are outside_dispersers (" << outside_dispersers.size()
             << ") but there should be none\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "Neighbor kernel test infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    if (mortality_tracker != expected_mortality_tracker) {
        cout << "Neighbor kernel test mortality tracker (actual, expected):\n"
             << mortality_tracker << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    return 0;
}

int test_with_reduced_stochasticity()
{
    Raster<int> infected = {{5, 0}, {0, 0}};
    Raster<int> mortality_tracker = {{0, 0}, {0, 0}};
    Raster<int> susceptible = {{10, 20}, {14, 15}};
    Raster<int> total_hosts = susceptible;
    Raster<double> temperature = {{5, 0}, {0, 0}};
    Raster<double> weather_coefficient = {{0, 0}, {0, 0}};
    std::vector<std::vector<int>> movements = {{0, 0, 1, 1, 2},
                                               {0, 1, 0, 0, 3}};
    std::vector<unsigned> movement_schedule = {1, 1};
    unsigned step = 1;
    unsigned last_index = 0;

    Raster<int> expected_mortality_tracker = {{0, 10}, {0, 0}};
    auto expected_infected = expected_mortality_tracker + infected;

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;
    bool weather = false;
    double reproductive_rate = 2;
    bool generate_stochasticity = false;
    bool establishment_stochasticity = false;
    bool movement_stochasticity = false;
    // We want everything to establish.
    double establishment_probability = 1;
    DeterministicNeighborDispersalKernel kernel(Direction::E);
    Simulation<Raster<int>, Raster<double>> simulation(
        42, infected.rows(), infected.cols(), model_type_from_string("SI"), 0,
        generate_stochasticity, establishment_stochasticity,
        movement_stochasticity);
    simulation.generate(dispersers, infected, weather, weather_coefficient,
                        reproductive_rate);
    auto expected_dispersers = reproductive_rate * infected;
    if (dispersers != expected_dispersers) {
        cout << "reduced_stochasticity: dispersers (actual, expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    simulation.disperse(dispersers, susceptible, infected, mortality_tracker,
                        total_hosts, outside_dispersers, weather,
                        weather_coefficient, kernel, establishment_probability);
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
    if (mortality_tracker != expected_mortality_tracker) {
        cout << "reduced_stochasticity: mortality tracker (actual, expected):\n"
             << mortality_tracker << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    infected = {{5, 0}, {0, 0}};
    susceptible = {{10, 20}, {14, 15}};
    mortality_tracker = {{0, 0}, {0, 0}};
    total_hosts = susceptible;
    simulation.movement(infected, susceptible, mortality_tracker, total_hosts,
                        step, last_index, movements, movement_schedule);
    expected_infected = {{4, 0}, {0, 1}};
    if (infected != expected_infected) {
        cout << "reduced_stochasticity: infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    return 0;
}

int disperse_and_infect_postcondition(int step,
                                      const std::vector<Raster<int>> &exposed)
{
    Raster<int> zeros(exposed[0].rows(), exposed[0].cols(), 0);
    if (exposed.back() != zeros) {
        cout << "SEI: disperse_and_infect post-condition not met in step "
             << step << "\n";
        return 1;
    }
    return 0;
}

int exposed_state(int step, const std::vector<Raster<int>> &exposed,
                  const Raster<int> &expected_exposed)
{
    int ret = 0;
    Raster<int> zeros(exposed[0].rows(), exposed[0].cols(), 0);
    for (unsigned int i = 0; i < exposed.size(); ++i) {
        if (int(i) >= int(exposed.size()) - step - 2 &&
            i < exposed.size() - 1) {
            if (exposed[i] != expected_exposed) {
                cout << "SEI test exposed[" << i << "] (actual, expected):\n"
                     << exposed[i] << "  !=\n"
                     << expected_exposed << "\n";
                print_vector(exposed);
                ret += 1;
            }
        }
        else {
            if (exposed[i] != zeros) {
                cout << "SEI test exposed[" << i
                     << "] (actual, expected zeros):\n"
                     << exposed[i] << "\n";
                print_vector(exposed);
                ret += 1;
            }
        }
    }
    return ret;
}

int test_with_sei()
{
    Raster<int> infected = {{5, 0}, {0, 0}};
    Raster<int> mortality_tracker = {{0, 0}, {0, 0}};
    // Susceptible and total are set in a way that there won't be any
    // dilution effect and the disperser will always establish given the
    // selected random seed. Establishment probability is high and with
    // the given seed we don't get any random numbers in establishment
    // test higher than that. (The weather is disabled.)
    Raster<int> susceptible = {{10, 6}, {14, 15}};
    // add a lot of hosts, so that exposing or infecting them won't
    // chanage the susceptible/total ratio much
    susceptible += 100000;
    // we want to minimize the dilution effect
    Raster<int> total_hosts = susceptible;
    Raster<double> temperature = {{5, 0}, {0, 0}};
    Raster<double> weather_coefficient = {{0, 0}, {0, 0}};
    Raster<int> zeros(infected.rows(), infected.cols(), 0);

    Raster<int> expected_infected = infected;
    Raster<int> expected_exposed = {{0, 10}, {0, 0}};

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;
    bool weather = false;
    double reproductive_rate = 2;
    unsigned latency_period_steps = 3;

    std::vector<Raster<int>> exposed(
        latency_period_steps + 1,
        Raster<int>(infected.rows(), infected.cols(), 0));

    DeterministicNeighborDispersalKernel kernel(Direction::E);
    Simulation<Raster<int>, Raster<double>> simulation(
        42, infected.rows(), infected.cols(),

        model_type_from_string("SEI"), latency_period_steps);
    dispersers = reproductive_rate * infected;
    int step = 0;
    int ret = 0;
    simulation.disperse_and_infect(
        step, dispersers, susceptible, exposed, infected, mortality_tracker,
        total_hosts, outside_dispersers, weather, weather_coefficient, kernel);
    if (infected != expected_infected) {
        cout << "SEI test infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        ret += 1;
    }
    if (mortality_tracker != zeros) {
        cout << "SEI test mortality tracker (actual, expected zeros):\n"
             << mortality_tracker << "\n";
        ret += 1;
    }
    print_vector(exposed);
    cout << infected << "\n\n";
    ret += disperse_and_infect_postcondition(step, exposed);
    simulation.disperse_and_infect(
        ++step, dispersers, susceptible, exposed, infected, mortality_tracker,
        total_hosts, outside_dispersers, weather, weather_coefficient, kernel);
    print_vector(exposed);
    cout << infected << "\n\n";
    ret += disperse_and_infect_postcondition(step, exposed);
    simulation.disperse_and_infect(
        ++step, dispersers, susceptible, exposed, infected, mortality_tracker,
        total_hosts, outside_dispersers, weather, weather_coefficient, kernel);
    print_vector(exposed);
    cout << infected << "\n\n";
    ret += disperse_and_infect_postcondition(step, exposed);
    if (!outside_dispersers.empty()) {
        cout << "SEI test: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        ret += 1;
    }
    exposed_state(step, exposed, expected_exposed);
    if (mortality_tracker != zeros) {
        cout << "SEI test mortality tracker (actual, expected zeros):\n"
             << mortality_tracker << "\n";
        ret += 1;
    }
    simulation.disperse_and_infect(
        ++step, dispersers, susceptible, exposed, infected, mortality_tracker,
        total_hosts, outside_dispersers, weather, weather_coefficient, kernel);
    print_vector(exposed);
    cout << infected << "\n\n";
    ret += disperse_and_infect_postcondition(step, exposed);
    expected_infected = expected_infected + expected_exposed;
    Raster<int> expected_mortality_tracker = expected_exposed;
    if (!outside_dispersers.empty()) {
        cout << "SEI test: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be none\n";
        ret += 1;
    }
    if (infected != expected_infected) {
        cout << "SEI test infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        ret += 1;
    }
    if (mortality_tracker != expected_mortality_tracker) {
        cout << "SEI test mortality tracker (actual, expected):\n"
             << mortality_tracker << "  !=\n"
             << expected_mortality_tracker << "\n";
        ret += 1;
    }
    exposed_state(step, exposed, expected_exposed);
    simulation.disperse_and_infect(
        ++step, dispersers, susceptible, exposed, infected, mortality_tracker,
        total_hosts, outside_dispersers, weather, weather_coefficient, kernel);
    print_vector(exposed);
    cout << infected << "\n\n";
    ret += disperse_and_infect_postcondition(step, exposed);

    for (int i = 0; i < 10; ++i) {
        simulation.disperse_and_infect(++step, dispersers, susceptible, exposed,
                                       infected, mortality_tracker, total_hosts,
                                       outside_dispersers, weather,
                                       weather_coefficient, kernel);
        print_vector(exposed);
        cout << infected << "\n\n";
        ret += disperse_and_infect_postcondition(step, exposed);
    }

    return ret;
}

int test_SI_versus_SEI0()
{
    Raster<int> infected_1 = {{5, 0}, {0, 0}};
    auto infected_2 = infected_1;
    auto infected_3 = infected_1;
    Raster<int> mortality_tracker_1 = {{0, 0}, {0, 0}};
    auto mortality_tracker_2 = mortality_tracker_1;
    auto mortality_tracker_3 = mortality_tracker_1;
    // Susceptible and total are set in a way that there won't be any
    // dilution effect and the disperser will always establish given the
    // selected random seed. Establishment probability is high and with
    // the given seed we don't get any random numbers in establishment
    // test higher than that. (The weather is disabled.)
    Raster<int> susceptible_1 = {{10, 6}, {14, 15}};
    // add a lot of hosts, so that exposing or infecting them won't
    // chanage the susceptible/total ratio much
    susceptible_1 += 100000;
    auto susceptible_2 = susceptible_1;
    auto susceptible_3 = susceptible_1;
    // we want to minimize the dilution effect
    auto total_hosts_1 = susceptible_1;
    auto total_hosts_2 = susceptible_2;
    auto total_hosts_3 = susceptible_3;
    Raster<double> temperature = {{5, 0}, {0, 0}};
    Raster<double> weather_coefficient = {{0, 0}, {0, 0}};
    auto rows = infected_1.rows();
    auto cols = infected_1.cols();

    std::vector<std::tuple<int, int>> outside_dispersers_1;
    auto outside_dispersers_2 = outside_dispersers_1;
    auto outside_dispersers_3 = outside_dispersers_1;
    bool weather = false;
    double reproductive_rate = 2;
    unsigned latency_period_steps = 0;

    auto dispersers = reproductive_rate * infected_1;
    std::vector<Raster<int>> empty_exposed;

    std::vector<Raster<int>> exposed(latency_period_steps + 1,
                                     Raster<int>(rows, cols, 0));

    DeterministicNeighborDispersalKernel kernel(Direction::E);
    Simulation<Raster<int>, Raster<double>> simulation_SI_1(
        42, rows, cols, model_type_from_string("SI"));
    Simulation<Raster<int>, Raster<double>> simulation_SI_2(
        42, rows, cols, model_type_from_string("SI"));
    Simulation<Raster<int>, Raster<double>> simulation_SEI0(
        42, rows, cols, model_type_from_string("SEI"), latency_period_steps);
    int ret = 0;
    for (int step = 0; step < 10; ++step) {
        simulation_SI_1.disperse_and_infect(
            step, dispersers, susceptible_1, empty_exposed, infected_1,
            mortality_tracker_1, total_hosts_1, outside_dispersers_1, weather,
            weather_coefficient, kernel);
        simulation_SI_2.disperse(dispersers, susceptible_2, infected_2,
                                 mortality_tracker_2, total_hosts_2,
                                 outside_dispersers_2, weather,
                                 weather_coefficient, kernel);
        simulation_SEI0.disperse_and_infect(
            step, dispersers, susceptible_3, exposed, infected_3,
            mortality_tracker_3, total_hosts_3, outside_dispersers_3, weather,
            weather_coefficient, kernel);
        ret += disperse_and_infect_postcondition(step, exposed);
        if (infected_2 != infected_1) {
            cout << "SI with disperse vs SI with disperse_and_infect: infected "
                    "don't fit\n";
            cout << infected_2;
            cout << infected_1;
            ret += 1;
        }
        if (infected_3 != infected_1) {
            cout << "SI with disperse_and_infect vs SEI0: infected don't fit\n";
            cout << infected_1;
            cout << infected_3;
            ret += 1;
        }
        if (infected_3 != infected_2) {
            cout << "SI with disperse vs SEI0: infected don't fit\n";
            cout << infected_2;
            cout << infected_3;
            ret += 1;
        }
    }

    return ret;
}

int test_calling_all_functions()
{
    Raster<int> infected = {{5, 0}, {0, 0}};
    Raster<int> mortality_tracker = {{0, 0}, {0, 0}};
    Raster<int> susceptible = {{10, 15}, {14, 15}};
    Raster<int> total_hosts = {{15, 15}, {14, 15}};
    Raster<double> temperature = {{5, 0}, {0, 0}};
    Raster<double> weather_coefficient = {{0.6, 0.8}, {0.2, 0.8}};
    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;
    DispersalKernelType dispersal_kernel = DispersalKernelType::Cauchy;
    bool weather = true;
    double lethal_temperature = -4.5;
    double reproductive_rate = 4.5;
    double short_distance_scale = 1.0;
    int ew_res = 30;
    int ns_res = 30;
    unsigned step = 1;
    unsigned last_index = 0;
    int seed = 42;
    std::vector<std::vector<int>> movements = {{0, 0, 1, 1, 2},
                                               {0, 1, 0, 0, 3}};
    std::vector<unsigned> movement_schedule = {1, 1};
    Simulation<Raster<int>, Raster<double>> simulation(seed, infected.rows(),
                                                       infected.cols());
    simulation.remove(infected, susceptible, temperature, lethal_temperature);
    simulation.generate(dispersers, infected, weather, weather_coefficient,
                        reproductive_rate);
    RadialDispersalKernel<Raster<int>> kernel(ew_res, ns_res, dispersal_kernel,
                                              short_distance_scale);
    simulation.movement(infected, susceptible, mortality_tracker, total_hosts,
                        step, last_index, movements, movement_schedule);
    simulation.disperse(dispersers, susceptible, infected, mortality_tracker,
                        total_hosts, outside_dispersers, weather,
                        weather_coefficient, kernel);
    cout << "outside_dispersers: " << outside_dispersers.size() << endl;
    return 0;
}

int main()
{
    int ret = 0;

    ret += test_rotate_left_by_one({2}, {2});
    ret += test_rotate_left_by_one({1, 2}, {2, 1});
    ret += test_rotate_left_by_one({1, 2, 3, 4, 5}, {2, 3, 4, 5, 1});

    ret += test_calling_all_functions();
    ret += test_with_neighbor_kernel();
    ret += test_with_reduced_stochasticity();
    ret += test_with_sei();
    ret += test_SI_versus_SEI0();

    return ret;
}

#endif // POPS_TEST
