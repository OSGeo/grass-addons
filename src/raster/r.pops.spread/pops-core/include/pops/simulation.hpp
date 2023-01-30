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
#include <vector>
#include <random>
#include <string>
#include <stdexcept>

#include "utils.hpp"

namespace pops {

/** Rotate elements in a container to the left by one
 *
 * Rotates (moves) elements in a container to the left (anticlockwise)
 * by one. The second element is moved to the front and the first
 * element is moved to the back.
 */
template <typename Container>
void rotate_left_by_one(Container &container)
{
    std::rotate(container.begin(), container.begin() + 1, container.end());
}

/** The type of a epidemiological model (SI or SEI)
 */
enum class ModelType {
    SusceptibleInfected,       ///< SI (susceptible - infected)
    SusceptibleExposedInfected ///< SEI (susceptible - exposed - infected)
};

/*! Get a corresponding enum value for a string which is a model type name.
 *
 * Throws an std::invalid_argument exception if the value was not
 * found or is not supported (which is the same thing).
 */
inline ModelType model_type_from_string(const std::string &text)
{
    if (text == "SI" || text == "SusceptibleInfected" ||
        text == "susceptible-infected" || text == "susceptible_infected")
        return ModelType::SusceptibleInfected;
    else if (text == "SEI" || text == "SusceptibleExposedInfected" ||
             text == "susceptible-exposed-infected" ||
             text == "susceptible_exposed_infected")
        return ModelType::SusceptibleExposedInfected;
    else
        throw std::invalid_argument("model_type_from_string: Invalid"
                                    " value '" +
                                    text + "' provided");
}

/*! Overload which allows to pass C-style string which is nullptr (NULL)
 *
 * @see model_type_from_string(const std::string& text)
 */
inline ModelType model_type_from_string(const char *text)
{
    // call the string version
    return model_type_from_string(text ? std::string(text) : std::string());
}

/*! The main class to control the spread simulation.
 *
 * The Simulation class handles the mechanics of the model, but the
 * timing of the events or steps should be handled outside of this
 * class unless noted otherwise. The notable exceptions are exposed
 * hosts in the SEI model type and mortality.
 *
 * The template parameters IntegerRaster and FloatRaster are raster
 * image or matrix types. Any 2D numerical array should work as long as
 * it uses function call operator to access the values, i.e. it provides
 * indexing for reading and writing values using `()`. In other words,
 * the operations such as the two following ones should be possible:
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
template <typename IntegerRaster, typename FloatRaster,
          typename RasterIndex = int>
class Simulation {
private:
    RasterIndex rows_;
    RasterIndex cols_;
    bool dispersers_stochasticity_;
    bool establishment_stochasticity_;
    bool movement_stochasticity_;
    ModelType model_type_;
    unsigned latency_period_;
    std::default_random_engine generator_;

public:
    /** Creates simulation object and seeds the internal random number
     * generator.
     *
     * The same random number generator is used throughout the simulation
     * and is seeded once at the beginning.
     *
     * The number or rows and columns needs to be the same as the size
     * of rasters used with the Simulation object
     * (potentially, it can be also smaller).
     *
     * @param model_type Type of the model (SI or SEI)
     * @param latency_period Length of the latency period in steps
     * @param random_seed Number to seed the random number generator
     * @param rows Number of rows
     * @param cols Number of columns
     * @param dispersers_stochasticity Enable stochasticity in generating of
     * dispersers
     * @param establishment_stochasticity Enable stochasticity in establishment
     * step
     * @param movement_stochasticity Enable stochasticity in movement of hosts
     */
    Simulation(unsigned random_seed, RasterIndex rows, RasterIndex cols,
               ModelType model_type = ModelType::SusceptibleInfected,
               unsigned latency_period = 0,
               bool dispersers_stochasticity = true,
               bool establishment_stochasticity = true,
               bool movement_stochasticity = true)
        : rows_(rows), cols_(cols),
          dispersers_stochasticity_(dispersers_stochasticity),
          establishment_stochasticity_(establishment_stochasticity),
          movement_stochasticity_(movement_stochasticity),
          model_type_(model_type), latency_period_(latency_period)
    {
        generator_.seed(random_seed);
    }

    Simulation() = delete;

    void remove(IntegerRaster &infected, IntegerRaster &susceptible,
                const FloatRaster &temperature, double lethal_temperature)
    {
        for (int i = 0; i < rows_; i++) {
            for (int j = 0; j < cols_; j++) {
                if (temperature(i, j) < lethal_temperature) {
                    // move infested/infected host back to susceptible pool
                    susceptible(i, j) += infected(i, j);
                    // remove all infestation/infection in the infected class
                    infected(i, j) = 0;
                }
            }
        }
    }

    void mortality(IntegerRaster &infected, double mortality_rate,
                   int current_year, int first_mortality_year,
                   IntegerRaster &mortality,
                   std::vector<IntegerRaster> &mortality_tracker_vector)
    {
        if (current_year >= (first_mortality_year)) {
            int mortality_current_year = 0;
            int max_year_index = current_year - first_mortality_year;

            for (int i = 0; i < rows_; i++) {
                for (int j = 0; j < cols_; j++) {
                    for (int year_index = 0; year_index <= max_year_index;
                         year_index++) {
                        int mortality_in_year_index = 0;
                        if (mortality_tracker_vector[year_index](i, j) > 0) {
                            mortality_in_year_index =
                                mortality_rate *
                                mortality_tracker_vector[year_index](i, j);
                            mortality_tracker_vector[year_index](i, j) -=
                                mortality_in_year_index;
                            mortality(i, j) += mortality_in_year_index;
                            mortality_current_year += mortality_in_year_index;
                            if (infected(i, j) > 0) {
                                infected(i, j) -= mortality_in_year_index;
                            }
                        }
                    }
                }
            }
        }
    }

    /** Moves hosts from one location to another
     *
     * @note Note that unlike the other functions, here, *total_hosts*,
     * i.e., number of hosts is required, not number of all hosts
     * and non-host individuals.
     *
     * @param infected Currently infected hosts
     * @param susceptible Currently susceptible hosts
     * @param mortality_tracker Hosts that are infected at a specific time step
     * @param total_hosts Total number of hosts
     * @param step the current step of the simulation
     * @param last_index the last index to not be used from movements
     * @param movements a vector of ints with row_from, col_from, row_to,
     * col_to, and num_hosts
     * @param movement_schedule a vector matching movements with the step at
     * which the movement from movements are applied
     *
     * @note Mortality and non-host individuals are not supported in movements.
     */
    unsigned movement(IntegerRaster &infected, IntegerRaster &susceptible,
                      IntegerRaster &mortality_tracker,
                      IntegerRaster &total_hosts, unsigned step,
                      unsigned last_index,
                      const std::vector<std::vector<int>> &movements,
                      std::vector<unsigned> movement_schedule)
    {
        UNUSED(mortality_tracker); // Mortality is not supported by movements.
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
            if (hosts > total_hosts(row_from, col_from)) {
                total_hosts_moved = total_hosts(row_from, col_from);
            }
            else {
                total_hosts_moved = hosts;
            }
            if (infected(row_from, col_from) > 0 &&
                susceptible(row_from, col_from) > 0) {
                inf_ratio = double(infected(row_from, col_from)) /
                            double(total_hosts(row_from, col_from));
                int infected_mean = total_hosts_moved * inf_ratio;
                if (infected_mean > 0) {
                    if (movement_stochasticity_) {
                        std::poisson_distribution<int> distribution(
                            infected_mean);
                        infected_moved = distribution(generator_);
                    }
                    else {
                        infected_moved = infected_mean;
                    }
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
            }
            else if (infected(row_from, col_from) > 0 &&
                     susceptible(row_from, col_from) == 0) {
                infected_moved = total_hosts_moved;
            }
            else if (infected(row_from, col_from) == 0 &&
                     susceptible(row_from, col_from) > 0) {
                susceptible_moved = total_hosts_moved;
            }
            else {
                continue;
            }

            infected(row_from, col_from) -= infected_moved;
            susceptible(row_from, col_from) -= susceptible_moved;
            total_hosts(row_from, col_from) -= total_hosts_moved;
            infected(row_to, col_to) += infected_moved;
            susceptible(row_to, col_to) += susceptible_moved;
            total_hosts(row_to, col_to) += total_hosts_moved;
        }
        return movements.size();
    }

    /** Generates dispersers based on infected
     *
     * @param[out] dispersers  (existing values are ignored)
     * @param infected Currently infected hosts
     * @param weather Whether to use the weather coefficient
     * @param weather_coefficient Spatially explicit weather coefficient
     * @param reproductive_rate reproductive rate (used unmodified when weather
     * coefficient is not used)
     */
    void generate(IntegerRaster &dispersers, const IntegerRaster &infected,
                  bool weather, const FloatRaster &weather_coefficient,
                  double reproductive_rate)
    {
        double lambda = reproductive_rate;
        for (int i = 0; i < rows_; i++) {
            for (int j = 0; j < cols_; j++) {
                if (infected(i, j) > 0) {
                    if (weather)
                        lambda = reproductive_rate * weather_coefficient(i, j);
                    int dispersers_from_cell = 0;
                    if (dispersers_stochasticity_) {
                        std::poisson_distribution<int> distribution(lambda);
                        for (int k = 0; k < infected(i, j); k++) {
                            dispersers_from_cell += distribution(generator_);
                        }
                    }
                    else {
                        dispersers_from_cell = lambda * infected(i, j);
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
     * Depending on what data is provided as the *exposed_or_infected*
     * paramater, this function can be part of the S to E step or the
     * S to I step.
     *
     * Typically, the generate() function is called beforehand to
     * create dispersers. In SEI model, the infect_exposed() function is
     * typically called afterwards.
     *
     * DispersalKernel is callable object or function with one parameter
     * which is the random number engine (generator). The return value
     * is row and column in the raster (or outside of it). The current
     * position is passed as parameters. The return value is in the
     * form of a tuple with row and column so that std::tie() is usable
     * on the result, i.e. function returning
     * `std::make_tuple(row, column)` fulfills this requirement.
     *
     * The *total_populations* can be total number of hosts in the basic case
     * or it can be the total size of population of all relevant species
     * both host and non-host if dilution effect should be applied.
     *
     * If establishment stochasticity is disabled,
     * *establishment_probability* is used to decide whether or not
     * a disperser is established in a cell. Value 1 means that all
     * dispresers will establish and value 0 means that no dispersers
     * will establish.
     *
     * @param[in] dispersers Dispersing individuals ready to be dispersed
     * @param[in,out] susceptible Susceptible hosts
     * @param[in,out] exposed_or_infected Exposed or infected hosts
     * @param[in,out] mortality_tracker Newly infected hosts (if applicable)
     * @param[in] total_populations All host and non-host individuals in the
     * area
     * @param[in,out] outside_dispersers Dispersers escaping the rasters
     * @param weather Whether or not weather coefficients should be used
     * @param[in] weather_coefficient Weather coefficient for each location
     * @param dispersal_kernel Dispersal kernel to move dispersers
     * @param establishment_probability Probability of establishment with no
     * stochasticity
     *
     * @note If the parameters or their default values don't correspond
     * with the disperse_and_infect() function, it is a bug.
     */
    template <typename DispersalKernel>
    void disperse(const IntegerRaster &dispersers, IntegerRaster &susceptible,
                  IntegerRaster &exposed_or_infected,
                  IntegerRaster &mortality_tracker,
                  const IntegerRaster &total_populations,
                  std::vector<std::tuple<int, int>> &outside_dispersers,
                  bool weather, const FloatRaster &weather_coefficient,
                  DispersalKernel &dispersal_kernel,
                  double establishment_probability = 0.5)
    {
        std::uniform_real_distribution<double> distribution_uniform(0.0, 1.0);
        int row;
        int col;

        for (int i = 0; i < rows_; i++) {
            for (int j = 0; j < cols_; j++) {
                if (dispersers(i, j) > 0) {
                    for (int k = 0; k < dispersers(i, j); k++) {
                        std::tie(row, col) = dispersal_kernel(generator_, i, j);

                        if (row < 0 || row >= rows_ || col < 0 ||
                            col >= cols_) {
                            // export dispersers dispersed outside of modeled
                            // area
                            outside_dispersers.emplace_back(
                                std::make_tuple(row, col));
                            continue;
                        }
                        if (susceptible(row, col) > 0) {
                            double probability_of_establishment =
                                (double)(susceptible(row, col)) /
                                total_populations(row, col);
                            double establishment_tester =
                                1 - establishment_probability;
                            if (establishment_stochasticity_)
                                establishment_tester =
                                    distribution_uniform(generator_);

                            if (weather)
                                probability_of_establishment *=
                                    weather_coefficient(i, j);
                            if (establishment_tester <
                                probability_of_establishment) {
                                exposed_or_infected(row, col) += 1;
                                susceptible(row, col) -= 1;
                                if (model_type_ ==
                                    ModelType::SusceptibleInfected) {
                                    mortality_tracker(row, col) += 1;
                                }
                                else if (model_type_ ==
                                         ModelType::
                                             SusceptibleExposedInfected) {
                                    // no-op
                                }
                                else {
                                    throw std::runtime_error(
                                        "Unknown ModelType value in "
                                        "Simulation::disperse()");
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /** Infect exposed hosts (E to I transition in the SEI model)
     *
     * Applicable to SEI model, no-operation otherwise, i.e., parameters
     * are left intact for other models.
     *
     * The exposed vector are the hosts exposed in the previous steps.
     * The length of the vector is the number of steps of the latency
     * period plus one. Before the first latency period is over,
     * the E to I transition won't happen because no item in the exposed
     * vector is old enough to become infected.
     *
     * The position of the items in the exposed vector determines their
     * age, i.e., for how long the hosts are exposed. The oldest item
     * is at the front and youngest at the end.
     * Before the the first latency period is over, items in the front
     * are still empty (unused) because no hosts were exposed for the
     * given time period.
     * After the first latency
     * period, this needs to be true before the function is called and
     * it is true after the function
     * finished with the difference that after the function is called,
     * the last item is empty in the sense that it does not contain any
     * hosts.
     *
     * When the E to I transition happens, hosts from the oldest item
     * in the exposed vector are moved to the infected (and mortality
     * tracker). They are removed from the exposed item and this item
     * is moved to the back of the vector.
     *
     * Like in disperse(), there is no distinction between *infected*
     * and *mortality_tracker*, but different usage is expected outside
     * of this function.
     *
     * The raster class used with the simulation class needs to support
     * `.fill()` method for this function to work.
     *
     * @param step Step in the simulation (>=0)
     * @param exposed Vector of exposed hosts
     * @param infected Infected hosts
     * @param mortality_tracker Newly infected hosts
     */
    void infect_exposed(unsigned step, std::vector<IntegerRaster> &exposed,
                        IntegerRaster &infected,
                        IntegerRaster &mortality_tracker)
    {
        if (model_type_ == ModelType::SusceptibleExposedInfected) {
            if (step >= latency_period_) {
                // Oldest item needs to be in the front
                auto &oldest = exposed.front();
                // Move hosts to infected raster
                infected += oldest;
                mortality_tracker += oldest;
                // Reset the raster
                // (hosts moved from the raster)
                oldest.fill(0);
            }
            // Age the items and the used one to the back
            // elements go one position to the left
            // new oldest goes to the front
            // old oldest goes to the back
            rotate_left_by_one(exposed);
        }
        else if (model_type_ == ModelType::SusceptibleInfected) {
            // no-op
        }
        else {
            throw std::runtime_error(
                "Unknown ModelType value in Simulation::infect_exposed()");
        }
    }

    /** Disperse, expose, and infect based on dispersers
     *
     * This function wraps disperse() and infect_exposed() for use in SI
     * and SEI models.
     *
     * In case of SEI model, before calling this function, last item in
     * the exposed vector needs to be ready to be used for exposure,
     * i.e., typically, it should be empty in the sense that there are
     * no hosts in the raster. This is normally taken care of by a
     * previous call to this function. The initial state of the exposed
     * vector should be such that size is latency period in steps plus 1
     * and each raster is empty, i.e., does not contain any hosts
     * (all values set to zero).
     *
     * See the infect_exposed() function for the details about exposed
     * vector, its size, and its items.
     *
     * See disperse() and infect_exposed() for a detailed list of
     * parameters and behavior. The disperse() parameter documentation
     * can be applied as is except that disperse() function's parameter
     * *exposed_or_infested* is expected to change based on the context
     * while this function's parameter *infected* is always the infected
     * individuals. Besides parameters from disperse(), this function
     * has parameter *exposed* which is the same as the one from the
     * infect_exposed() function.
     */
    template <typename DispersalKernel>
    void disperse_and_infect(
        unsigned step, const IntegerRaster &dispersers,
        IntegerRaster &susceptible, std::vector<IntegerRaster> &exposed,
        IntegerRaster &infected, IntegerRaster &mortality_tracker,
        const IntegerRaster &total_populations,
        std::vector<std::tuple<int, int>> &outside_dispersers, bool weather,
        const FloatRaster &weather_coefficient,
        DispersalKernel &dispersal_kernel,
        double establishment_probability = 0.5)
    {
        auto *infected_or_exposed = &infected;
        if (model_type_ == ModelType::SusceptibleExposedInfected) {
            // The empty - not yet exposed - raster is in the back
            // and will become youngest exposed one.
            infected_or_exposed = &exposed.back();
        }
        this->disperse(dispersers, susceptible, *infected_or_exposed,
                       mortality_tracker, total_populations, outside_dispersers,
                       weather, weather_coefficient, dispersal_kernel,
                       establishment_probability);
        if (model_type_ == ModelType::SusceptibleExposedInfected) {
            this->infect_exposed(step, exposed, infected, mortality_tracker);
        }
    }
};

} // namespace pops

#endif // POPS_SIMULATION_HPP
