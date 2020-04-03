/*
 * PoPS model - pest or pathogen spread simulation
 *
 * Copyright (C) 2015-2020 by the authors.
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
 *
 * Template parameter RasterIndex is type used for maximum indices of
 * the used rasters and should be the same as what the actual raster
 * types are using. However, at the same time, comparison with signed
 * type are perfomed and a signed type might be required in the future.
 * A default is provided, but it can be changed in the future.
 */
template<typename IntegerRaster, typename FloatRaster, typename RasterIndex = int>
class Simulation
{
private:
    RasterIndex rows_;
    RasterIndex cols_;
    std::default_random_engine generator_;
public:

    /** Creates simulation object and seeds the internal random number generator.
     *
     * The same random number generator is used throughout the simulation
     * and is seeded once at the beginning.
     *
     * The number or rows and columns needs to be the same as the size
     * of rasters used with the Simulation object
     * (potentially, it can be also smaller).
     *
     * @param random_seed Number to seed the random number generator
     * @param rows Number of rows
     * @param cols Number of columns
     */
    Simulation(unsigned random_seed,
               RasterIndex rows,
               RasterIndex cols)
        :
          rows_(rows),
          cols_(cols)
    {
        generator_.seed(random_seed);
    }

    Simulation() = delete;

    void remove(IntegerRaster& infected,
                IntegerRaster& susceptible,
                const FloatRaster& temperature,
                double lethal_temperature)
    {
        for (int i = 0; i < rows_; i++) {
            for (int j = 0; j < cols_; j++) {
                if (temperature(i, j) < lethal_temperature) {
                    susceptible(i, j) += infected(i, j);  // move infested/infected host back to suseptible pool
                    infected(i, j) = 0;  // remove all infestation/infection in the infected class
                }
            }
        }
    }
    
    void mortality(IntegerRaster& infected,
                   double mortality_rate,
                   int current_year,
                   int first_mortality_year,
                   IntegerRaster& mortality,
                   std::vector<IntegerRaster>& mortality_tracker_vector)
    {
        if (current_year >= (first_mortality_year)) {
            int mortality_current_year = 0;
            int max_year_index = current_year - first_mortality_year;
            
            for (int i = 0; i < rows_; i++) {
                for (int j = 0; j < cols_; j++) {
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

    /** Moves hosts from one location to another
     *
     * @param infected Currently infected hosts
     * @param susceptible Currently susceptible hosts
     * @param mortality_tracker Hosts that are infected at a specific time step
     * @param total_plants 
     * @param step the current step of the simulation
     * @param last_index the last index to not be used from movements
     * @param movements a vector of ints with row_from, col_from, row_to, col_to, and num_hosts
     * @param movement_schedule a vector matching movements with the step at which the movement from movements are applied
     */
    unsigned movement(IntegerRaster& infected,
                      IntegerRaster& susceptible, 
                      IntegerRaster& mortality_tracker,
                      IntegerRaster& total_plants,
                      unsigned step, unsigned last_index,
                      const std::vector<std::vector<int>>& movements,
                      std::vector<unsigned> movement_schedule)
    {
        for (unsigned i = last_index; i < movements.size(); i++) {
            auto moved = movements[i];
            unsigned move_schedule = movement_schedule[i];
            if (move_schedule != step) {
                return i;
            }
            int infected_moved = 0;
            int susceptible_moved = 0;
            int total_hosts_moved = 0;
            double inf_ratio = 0;
            int row_from = moved[0];
            int col_from = moved[1];
            int row_to = moved[2];
            int col_to = moved[3];
            int hosts = moved[4];
            if (hosts > total_plants(row_from, col_from)) {
                total_hosts_moved = total_plants(row_from, col_from);
            } else {
                total_hosts_moved = hosts;
            }
            if (infected(row_from, col_from) > 0 && susceptible(row_from, col_from) > 0) {
                inf_ratio = double(infected(row_from, col_from)) / double(total_plants(row_from, col_from));
                int infected_mean = total_hosts_moved * inf_ratio;
                if (infected_mean > 0) {
                    std::poisson_distribution<int> distribution(infected_mean);
                    infected_moved = distribution(generator_);
                }
                if (infected_moved > infected(row_from, col_from)) {
                    infected_moved = infected(row_from, col_from);
                } 
                if (infected_moved > total_hosts_moved) {
                  infected_moved = total_hosts_moved;
                }
                susceptible_moved = total_hosts_moved - infected_moved;
                if (susceptible_moved > susceptible(row_from, col_from)) {
                    susceptible_moved = susceptible(row_from, col_from);
                } 
            } else if (infected(row_from, col_from) > 0 && susceptible(row_from, col_from) == 0) {
                infected_moved = total_hosts_moved;
            } else if(infected(row_from, col_from) == 0 && susceptible(row_from, col_from) > 0) {
                susceptible_moved = total_hosts_moved;
            } else {
                continue;
            }
            
            infected(row_from, col_from) -= infected_moved;
            susceptible(row_from, col_from) -= susceptible_moved;
            total_plants(row_from, col_from) -= total_hosts_moved;
            infected(row_to, col_to) += infected_moved;
            susceptible(row_to, col_to) += susceptible_moved;
            total_plants(row_to, col_to) += total_hosts_moved;
        }
      return movements.size();
    }
    
    
    /** Generates dispersers based on infected
     *
     * @param[out] dispersers  (existing values are ignored)
     * @param infected Currently infected hosts
     * @param weather Whether to use the weather coefficient
     * @param weather_coefficient Spatially explicit weather coefficient
     * @param reproductive_rate reproductive rate (used unmodified when weather coefficient is not used)
     */
    void generate(IntegerRaster& dispersers,
                  const IntegerRaster& infected,
                  bool weather,
                  const FloatRaster& weather_coefficient,
                  double reproductive_rate)
    {
        double lambda = reproductive_rate;
        for (int i = 0; i < rows_; i++) {
            for (int j = 0; j < cols_; j++) {
                if (infected(i, j) > 0) {
                    if (weather)
                        lambda = reproductive_rate * weather_coefficient(i, j); // calculate 
                    int dispersers_from_cell = 0;
                    std::poisson_distribution<int> distribution(lambda);
                    
                    for (int k = 0; k < infected(i, j); k++) {
                        dispersers_from_cell += distribution(generator_);
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
     * Typically, the generate() function is called beforehand to
     * create dispersers.
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
    void disperse(const IntegerRaster& dispersers,
                  IntegerRaster& susceptible,
                  IntegerRaster& infected,
                  IntegerRaster& mortality_tracker,
                  const IntegerRaster& total_plants,
                  std::vector<std::tuple<int, int>>& outside_dispersers,
                  bool weather,
                  const FloatRaster& weather_coefficient,
                  DispersalKernel& dispersal_kernel)
    {
        std::uniform_real_distribution<double> distribution_uniform(0.0, 1.0);
        int row;
        int col;

        for (int i = 0; i < rows_; i++) {
            for (int j = 0; j < cols_; j++) {
                if (dispersers(i, j) > 0) {
                    for (int k = 0; k < dispersers(i, j); k++) {

                        std::tie(row, col) = dispersal_kernel(generator_, i, j);

                        if (row < 0 || row >= rows_ || col < 0 || col >= cols_) {
                            // export dispersers dispersed outside of modeled area
                            outside_dispersers.emplace_back(std::make_tuple(row, col));
                            continue;
                        }
                        if (susceptible(row, col) > 0) {
                            double probability_of_establishment =
                                    (double)(susceptible(row, col)) /
                                    total_plants(row, col);
                            double establishment_tester = distribution_uniform(generator_);

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
