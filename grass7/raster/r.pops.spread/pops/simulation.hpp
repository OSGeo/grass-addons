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

#include <cmath>
#include <tuple>
#include <random>

using std::cerr;
using std::endl;

namespace pops {

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
    IntegerRaster dispersers;
    std::default_random_engine generator;
public:

    Simulation(unsigned random_seed, const IntegerRaster &size)
        :
          width(size.cols()),
          height(size.rows()),
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

    /** Creates dispersal locations for the dispersing individuals
     *
     * Assumes that the generate() function was called beforehand.
     *
     * DispersalKernel is callable object or function with one parameter
     * which is the random number engine (generator). The return value
     * is row and column in the raster (or outside of it). The current
     * position is passed as parameters. The return valus is in the
     * form of a tuple with row and column so that std::tie() is usable
     * on the result, i.e. function returning
     * `std::make_tuple(row, column)` fulfills this requirement.
     */
    template<typename DispersalKernel>
    void disperse(IntegerRaster& susceptible, IntegerRaster& infected,
                  IntegerRaster& mortality_tracker,
                  const IntegerRaster& total_plants,
                  std::vector<std::tuple<int, int>>& outside_dispersers,
                  bool weather, const FloatRaster& weather_coefficient,
                  DispersalKernel& dispersal_kernel)
    {
        std::uniform_real_distribution<double> distribution_uniform(0.0, 1.0);
        int row;
        int col;

        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                if (dispersers(i, j) > 0) {
                    for (int k = 0; k < dispersers(i, j); k++) {

                        std::tie(row, col) = dispersal_kernel(generator, i, j);

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
