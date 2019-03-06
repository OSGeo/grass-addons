/*
 * SOD model - spore simulation
 *
 * Copyright (C) 2015-2017 by the authors.
 *
 * Authors: Zexi Chen (zchen22 ncsu edu)
 *          Vaclav Petras (wenzeslaus gmail com)
 *          Anna Petrasova (kratochanna gmail com)
 *          Chris Jones (cjones1688 gmail com)
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_SIMULATION_HPP
#define POPS_SIMULATION_HPP

#include "raster.hpp"

#include <cmath>
#include <tuple>
#include <random>

// PI is used in the code and M_PI is not guaranteed
// fix it, but prefer the system definition
#ifndef M_PI
    #define M_PI 3.14159265358979323846
#endif
#ifndef PI
    #define PI M_PI
#endif

using std::cerr;
using std::endl;

namespace pops {

/*! Von Mises Distribution (Circular data distribution)

    mu is the mean angle, expressed in radians between 0 and 2*pi,
    and kappa is the concentration parameter, which must be greater
    than or equal to zero. If kappa is equal to zero, this distribution
    reduces to a uniform random angle over the range 0 to 2*pi.
*/
class von_mises_distribution
{
public:
    von_mises_distribution(double mu, double kappa)
        : mu(mu), kappa(kappa), distribution(0.0, 1.0)
    {}
    template<class Generator>
    double operator ()(Generator& generator)
    {
        double a, b, c, f, r, theta, u1, u2, u3, z;

        if (kappa <= 1.e-06)
            return 2 * PI * distribution(generator);

        a = 1.0 + sqrt(1.0 + 4.0 * kappa * kappa);
        b = (a - sqrt(2.0 * a)) / (2.0 * kappa);
        r = (1.0 + b * b) / (2.0 * b);

        while (true) {
            u1 = distribution(generator);
            z = cos(PI * u1);
            f = (1.0 + r * z) / (r + z);
            c = kappa * (r - f);
            u2 = distribution(generator);
            if (u2 <= c * (2.0 - c) || u2 < c * exp(1.0 - c))
                break;
        }

        u3 = distribution(generator);
        if (u3 > 0.5) {
            theta = fmod(mu + acos(f), 2 * PI);
        }
        else {
            theta = fmod(mu - acos(f), 2 * PI);
        }
        return theta;
    }
private:
    double mu;
    double kappa;
    std::uniform_real_distribution<double> distribution;
};

enum DispersalKernel
{
    CAUCHY, CAUCHY_DOUBLE_SCALE
};

// NONE means that there is no wind
enum Direction
{
    N = 0, NE = 45, E = 90, SE = 135, S = 180, SW = 225, W = 270, NW = 315, NONE
};

/*! The main class to control the spread simulation.
 *
 * The template parameters IntegerRaster and FloatRaster are raster
 * image or matrix types. Any 2D numerical array should work as long as
 * it uses function call operator to access the values, i.e. it provides
 * indexing for reading and writing values using `()`. In other words,
 * the two following operations should be possible:
 *
 * ```
 * a(i, j) = 1;
 * a(i, j) == 1;
 * ```
 *
 * The PoPS library offers a Raster template class to fill this role,
 * but other classes can be used as well.
 */
template<typename IntegerRaster, typename FloatRaster>
class Simulation
{
private:
    int width;
    int height;
    // the west-east resolution of the pixel
    int west_east_resolution;
    // the north-south resolution of the pixel
    int north_south_resolution;
    IntegerRaster dispersers;
    std::default_random_engine generator;
public:

    Simulation(unsigned random_seed, const IntegerRaster &size, double ew_res, double ns_res)
        :
          width(size.cols()),
          height(size.rows()),
          west_east_resolution(ew_res),
          north_south_resolution(ns_res),
          dispersers(height, width)
    {
        generator.seed(random_seed);
    }

    Simulation() = delete;

    void remove(IntegerRaster& infected, IntegerRaster& susceptible,
                const FloatRaster& temperature,
                double lethal_temperature)
    {
        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                if (temperature(i, j) < lethal_temperature) {
                    susceptible(i, j) += infected(i, j);  // move infested/infected host back to suseptible pool
                    infected(i, j) = 0;  // remove all infestation/infection in the infected class
                }
            }
        }
    }
    
    void mortality(IntegerRaster& infected, double mortality_rate, 
                   int current_year, int first_mortality_year,
                   IntegerRaster& mortality, std::vector<IntegerRaster>& mortality_tracker_vector)
    {
        if (current_year >= (first_mortality_year)) {
            int mortality_current_year = 0;
            int max_year_index = current_year - first_mortality_year;
            
            for (int i = 0; i < height; i++) {
                for (int j = 0; j < width; j++) {
                    for (unsigned year_index = 0; year_index <= max_year_index; year_index++) {
                      int mortality_in_year_index = 0;
                        if (mortality_tracker_vector[year_index](i, j) > 0) {
                            mortality_in_year_index = mortality_rate*mortality_tracker_vector[year_index](i,j);
                            mortality_tracker_vector[year_index](i,j) -= mortality_in_year_index;
                            mortality(i,j) += mortality_in_year_index;
                            mortality_current_year += mortality_in_year_index;
                            if (infected(i,j) > 0) {
                                infected(i,j) -= mortality_in_year_index;
                            }
                        }
                    }
                }
            }
        }
    }
    
    void generate(const IntegerRaster& infected,
                  bool weather, const FloatRaster& weather_coefficient,
                  double reproductive_rate)
    {
        double lambda = reproductive_rate;
        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                if (infected(i, j) > 0) {
                    if (weather)
                        lambda = reproductive_rate * weather_coefficient(i, j); // calculate 
                    int dispersers_from_cell = 0;
                    std::poisson_distribution<int> distribution(lambda);
                    
                    for (int k = 0; k < infected(i, j); k++) {
                        dispersers_from_cell += distribution(generator);
                    }
                    dispersers(i, j) = dispersers_from_cell;
                }
                else {
                    dispersers(i, j) = 0;
                }
            }
        }
    }

    void disperse(IntegerRaster& susceptible, IntegerRaster& infected,
                  IntegerRaster& mortality_tracker,
                  const IntegerRaster& total_plants,
                  std::vector<std::tuple<int, int>>& outside_dispersers,
                  bool weather, const FloatRaster& weather_coefficient,
                  DispersalKernel dispersal_kernel, double short_distance_scale,
                  double percent_short_distance_dispersal = 0.0,
                  double long_distance_scale = 0.0,
                  Direction wind_direction = NONE, double kappa = 2)
    {
        std::cauchy_distribution < double >distribution_cauchy_one(0.0, short_distance_scale);
        std::cauchy_distribution < double >distribution_cauchy_two(0.0, long_distance_scale);
    
        std::bernoulli_distribution distribution_bern(percent_short_distance_dispersal);
        std::uniform_real_distribution < double >distribution_uniform(0.0, 1.0);

        if (wind_direction == NONE)
            kappa = 0;
        von_mises_distribution vonmisesvariate(wind_direction * PI / 180, kappa);

        double distance = 0;
        double theta = 0;

        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                if (dispersers(i, j) > 0) {
                    for (int k = 0; k < dispersers(i, j); k++) {

                        // generate the distance from cauchy distribution or cauchy mixture distribution
                        if (dispersal_kernel == CAUCHY) {
                            distance = abs(distribution_cauchy_one(generator));
                        }
                        else if (dispersal_kernel == CAUCHY_DOUBLE_SCALE) {
                            // use bernoulli distribution to act as the sampling with prob(gamma,1-gamma)
                            if (distribution_bern(generator)) {
                                distance = abs(distribution_cauchy_one(generator));
                            }
                            else {
                                distance = abs(distribution_cauchy_two(generator));
                            }
                        }
                        else {
                            cerr <<
                                    "The paramter dispersal_kernel muse be set as either CAUCHY OR CAUCHY_DOUBLE_SCALE"
                                 << endl;
                            exit(EXIT_FAILURE);
                        }

                        theta = vonmisesvariate(generator);

                        int row = i - round(distance * cos(theta) / north_south_resolution);
                        int col = j + round(distance * sin(theta) / west_east_resolution);

                        if (row < 0 || row >= height || col < 0 || col >= width) {
                            // export dispersers dispersed outside of modeled area
                            outside_dispersers.emplace_back(std::make_tuple(row, col));
                            continue;
                        }
                        if (susceptible(row, col) > 0) {
                            double probability_of_establishment =
                                    (double)(susceptible(row, col)) /
                                    total_plants(row, col);
                            double establishment_tester = distribution_uniform(generator);

                            if (weather)
                                probability_of_establishment *= weather_coefficient(i, j);
                            if (establishment_tester < probability_of_establishment) {
                                infected(row, col) += 1;
                                mortality_tracker(row, col) += 1;
                                susceptible(row, col) -= 1;
                            }
                        }
                    }
                }
            }
        }
    }

};

} // namespace pops

#endif // POPS_SIMULATION_HPP