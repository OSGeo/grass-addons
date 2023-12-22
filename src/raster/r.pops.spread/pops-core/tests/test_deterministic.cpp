#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS deterministic_kernel class.
 *
 * Copyright (C) 2018-2020 by the authors.
 *
 * Authors: Margaret Lawrimore <malawrim ncsu edu>
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

#include <pops/radial_kernel.hpp>
#include <pops/simulation.hpp>

using std::cout;
using std::string;

using namespace pops;

int test_with_cauchy_deterministic_kernel()
{
    Raster<int> infected = {{5, 0, 0}, {0, 5, 0}, {0, 0, 2}};
    Raster<int> mortality_tracker = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}};
    Raster<int> susceptible = {{10, 20, 9}, {14, 15, 0}, {3, 0, 2}};
    Raster<int> total_hosts = susceptible;
    Raster<double> temperature = {{5, 0, 0}, {0, 0, 0}, {0, 0, 2}};
    Raster<double> weather_coefficient = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}};
    std::vector<std::vector<int>> movements = {
        {0, 0, 1, 1, 2}, {0, 1, 0, 0, 3}, {0, 1, 1, 0, 2}};
    std::vector<unsigned> movement_schedule = {1, 1};

    Raster<int> expected_mortality_tracker = {
        {10, 0, 0}, {0, 10, 0}, {0, 0, 2}};
    Raster<int> expected_infected = {{15, 0, 0}, {0, 15, 0}, {0, 0, 4}};

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;
    bool weather = false;
    double reproductive_rate = 2;
    bool generate_stochasticity = false;
    bool establishment_stochasticity = false;
    // We want everything to establish.
    double establishment_probability = 1;
    // Cauchy
    Simulation<Raster<int>, Raster<double>> simulation(
        42, infected.rows(), infected.cols(), model_type_from_string("SI"), 0,
        generate_stochasticity, establishment_stochasticity);
    simulation.generate(dispersers, infected, weather, weather_coefficient,
                        reproductive_rate);
    auto expected_dispersers = reproductive_rate * infected;
    if (dispersers != expected_dispersers) {
        cout << "Deterministic Kernel Cauchy: dispersers (actual, expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    RadialDispersalKernel<Raster<int>> deterministicKernel(
        30, 30, DispersalKernelType::Cauchy, 0.9, Direction::None, 0.0, true,
        dispersers, 0.9);
    // using a smaller scale value since the test raster is so small
    simulation.disperse(dispersers, susceptible, infected, mortality_tracker,
                        total_hosts, outside_dispersers, weather,
                        weather_coefficient, deterministicKernel,
                        establishment_probability);
    if (outside_dispersers.size() != 0) {
        cout << "Deterministic Kernel Cauchy: There are outside_dispersers ("
             << outside_dispersers.size() << ") but there should be 0\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "Deterministic Kernel Cauchy: infected (actual, expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    if (mortality_tracker != expected_mortality_tracker) {
        cout << "Deterministic Kernel Cauchy: mortality tracker (actual, "
                "expected):\n"
             << mortality_tracker << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    return 0;
}

int test_with_exponential_deterministic_kernel()
{
    Raster<int> infected = {{5, 0, 0}, {0, 5, 0}, {0, 0, 2}};
    Raster<int> mortality_tracker = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}};
    Raster<int> susceptible = {{10, 20, 9}, {14, 15, 0}, {3, 0, 2}};
    Raster<int> total_hosts = susceptible;
    Raster<double> movements = {
        {0, 0, 1, 1, 2}, {0, 1, 0, 0, 3}, {0, 1, 1, 0, 2}};
    Raster<double> temperature = {{5, 0, 0}, {0, 0, 0}, {0, 0, 2}};
    Raster<double> weather_coefficient = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}};
    std::vector<unsigned> movement_schedule = {1, 1};

    Raster<int> expected_mortality_tracker = {
        {10, 0, 0}, {0, 10, 0}, {0, 0, 2}};
    Raster<int> expected_infected = {{15, 0, 0}, {0, 15, 0}, {0, 0, 4}};

    Raster<int> dispersers(infected.rows(), infected.cols());
    std::vector<std::tuple<int, int>> outside_dispersers;

    bool weather = false;
    double reproductive_rate = 2;
    bool generate_stochasticity = false;
    bool establishment_stochasticity = false;
    // We want everything to establish.
    double establishment_probability = 1;
    // Exponential
    Simulation<Raster<int>, Raster<double>> s2(
        42, infected.rows(), infected.cols(), model_type_from_string("SI"), 0,
        generate_stochasticity, establishment_stochasticity);
    s2.generate(dispersers, infected, weather, weather_coefficient,
                reproductive_rate);
    auto expected_dispersers = reproductive_rate * infected;
    if (dispersers != expected_dispersers) {
        cout << "Deterministic Kernel Exponential: dispersers (actual, "
                "expected):\n"
             << dispersers << "  !=\n"
             << expected_dispersers << "\n";
        return 1;
    }
    RadialDispersalKernel<Raster<int>> deterministicKernel(
        30, 30, DispersalKernelType::Exponential, 1.0, Direction::None, 0.0,
        true, dispersers, 0.99);

    s2.disperse(dispersers, susceptible, infected, mortality_tracker,
                total_hosts, outside_dispersers, weather, weather_coefficient,
                deterministicKernel, establishment_probability);
    if (outside_dispersers.size() != 0) {
        cout << "Deterministic Kernel Exponential: There are "
                "outside_dispersers ("
             << outside_dispersers.size() << ") but there should be 0\n";
        return 1;
    }
    if (infected != expected_infected) {
        cout << "Deterministic Kernel Exponential: infected (actual, "
                "expected):\n"
             << infected << "  !=\n"
             << expected_infected << "\n";
        return 1;
    }
    if (mortality_tracker != expected_mortality_tracker) {
        cout << "Deterministic Kernel Exponential: mortality tracker (actual, "
                "expected):\n"
             << mortality_tracker << "  !=\n"
             << expected_mortality_tracker << "\n";
        return 1;
    }
    return 0;
}

int test_cauchy_distribution_functions()
{
    // testing cauchy pdf & icdf
    double scale = 0.001; // rounding to thousands place
    CauchyDistribution cauchy(1.0);
    double probability = (int)(cauchy.pdf(5) / scale) * scale;
    double probability_ref = 0.012;
    if (probability != probability_ref) {
        cout << "Cauchy Distribution: probability was " << probability
             << " but should be " << probability_ref << "\n";
        return 1;
    }
    double x = (int)(cauchy.icdf(0.98) / scale) * scale;
    double x_ref = 15.894;
    if (x != x_ref) {
        cout << "Cauchy Distribution: x was " << x << " but should be " << x_ref
             << "\n";
        return 1;
    }
    CauchyDistribution cauchy1(1.5);
    probability_ref = 0.017;
    probability = (int)(cauchy1.pdf(5) / scale) * scale;
    if (probability != probability_ref) {
        cout << "Cauchy Distribution: probability was " << probability
             << " but should be " << probability_ref << "\n";
        return 1;
    }
    x = (int)(cauchy1.icdf(0.98) / scale) * scale;
    x_ref = 23.841;
    if (x != x_ref) {
        cout << "Cauchy Distribution: x was " << x << " but should be " << x_ref
             << "\n";
        return 1;
    }
    return 0;
}

int test_exponential_distribution_functions()
{
    double scale = 0.001; // rounding to thousands place
    // testing exponential pdf & icdf
    ExponentialDistribution exponential(1.0);
    double probability = (int)(exponential.pdf(1) / scale) * scale;
    double probability_ref = 0.367;
    if (probability != probability_ref) {
        cout << "Exponential Distribution: probability was " << probability
             << " but should be " << probability_ref << "\n";
        return 1;
    }
    double x = (int)(exponential.icdf(0.98) / scale) * scale;
    double x_ref = 3.912;
    if (x != x_ref) {
        cout << "Exponential Distribution: x was " << x << " but should be "
             << x_ref << "\n";
        return 1;
    }
    ExponentialDistribution exponential2(1.5);
    probability = (int)(exponential2.pdf(1) / scale) * scale;
    probability_ref = 0.342;
    if (probability != probability_ref) {
        cout << "Exponential Distribution: probability was " << probability
             << " but should be " << probability_ref << "\n";
        return 1;
    }
    x = (int)(exponential2.icdf(0.98) / scale) * scale;
    x_ref = 5.868;
    if (x != x_ref) {
        cout << "Exponential Distribution: x was " << x << " but should be "
             << x_ref << "\n";
        return 1;
    }
    return 0;
}

int main()
{
    int ret = 0;

    ret += test_with_exponential_deterministic_kernel();
    ret += test_with_cauchy_deterministic_kernel();
    ret += test_cauchy_distribution_functions();
    ret += test_exponential_distribution_functions();

    std::cout << "Test deterministic number of errors: " << ret << std::endl;
    return ret;
}
#endif // POPS_TEST
