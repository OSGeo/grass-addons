/*
 * PoPS model - deterministic dispersal kernel
 *
 * Copyright (C) 2015-2020 by the authors.
 *
 * Authors: Margaret Lawrimore (malawrim ncsu edu)
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_DETERMINISTIC_KERNEL_HPP
#define POPS_DETERMINISTIC_KERNEL_HPP

#include <vector>
#include <tuple>

#include "raster.hpp"
#include "kernel_types.hpp"
#include "utils.hpp"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#ifndef PI
#define PI M_PI
#endif

namespace pops {

using std::abs;
using std::ceil;
using std::exp;
using std::log;
using std::pow;
using std::tan;

/*!
 * Cauchy distribution
 * Includes probability density function and inverse cumulative distribution
 * function pdf returns the probability that the variate has the value x icdf
 * returns the upper range that encompasses x percent of the distribution (e.g
 * for 99% input .99)
 */
class CauchyDistribution {
public:
    CauchyDistribution(double scale) : s(scale) {}

    double pdf(double x) { return 1 / ((s * M_PI) * (1 + (pow(x / s, 2)))); }
    // Inverse cdf (quantile function)
    double icdf(double x) { return s * tan(M_PI * (x - 0.5)); }

private:
    // scale parameter - 1 for standard
    double s;
};

/*!
 * Exponential distribution
 * Includes probability density function and inverse cumulative distribution
 * function pdf returns the probability that the variate has the value x icdf
 * returns the upper range that encompasses x percent of the distribution (e.g
 * for 99% input 0.99)
 */
class ExponentialDistribution {
public:
    ExponentialDistribution(double scale) : beta(scale) {}
    // assumes mu is 0 which is traditionally accepted
    double pdf(double x) { return (1 / beta) * (exp(-x / beta)); }
    // Inverse cdf (quantile function)
    double icdf(double x)
    {
        if (beta == 1) {
            return -log(1 - x);
        }
        else {
            return -beta * log(1 - x);
        }
    }

private:
    // scale parameter - 1 for standard
    // equal to 1/lambda
    double beta;
};

/*!
 * Dispersal kernel for deterministic spread to cell with highest probability of
 * spread
 *
 * Dispersal Kernel type determines use of Exponential or Cauchy distribution
 * to find probability.
 *
 * dispersal_percentage is the percent of all possible dispersal to be included
 * in the moving window size (e.g for 99% input 0.99).
 *
 * Useful for testing as it is deterministic and provides fully replicable
 * results
 */
template <typename IntegerRaster>
class DeterministicDispersalKernel {
protected:
    const IntegerRaster &dispersers_;
    // row/col position of middle cell
    int mid_row = 0;
    int mid_col = 0;
    // position of cell from previous call
    int prev_row = -1;
    int prev_col = -1;
    // number of rows/cols in the probability window
    int number_of_rows = 0;
    int number_of_columns = 0;
    // maximum distance from center cell to outer cells
    double max_distance{0};
    Raster<double> probability;
    Raster<double> probability_copy;
    CauchyDistribution cauchy;
    ExponentialDistribution exponential;
    DispersalKernelType kernel_type_;
    double proportion_of_dispersers;
    // the west-east resolution of the pixel
    double east_west_resolution;
    // the north-south resolution of the pixel
    double north_south_resolution;

public:
    DeterministicDispersalKernel(DispersalKernelType dispersal_kernel,
                                 const IntegerRaster &dispersers,
                                 double dispersal_percentage, double ew_res,
                                 double ns_res, double distance_scale)
        : dispersers_(dispersers), cauchy(distance_scale),
          exponential(distance_scale), kernel_type_(dispersal_kernel),
          east_west_resolution(ew_res), north_south_resolution(ns_res)
    {
        // We initialize max distance only for the supported kernels.
        // For the others, we report the error only when really called
        // to allow use of this class in initialization phase.
        if (kernel_type_ == DispersalKernelType::Cauchy) {
            max_distance = cauchy.icdf(dispersal_percentage);
        }
        else if (kernel_type_ == DispersalKernelType::Exponential) {
            max_distance = exponential.icdf(dispersal_percentage);
        }
        number_of_columns = ceil(max_distance / east_west_resolution) * 2 + 1;
        number_of_rows = ceil(max_distance / north_south_resolution) * 2 + 1;
        Raster<double> prob_size(number_of_rows, number_of_columns, 0);
        probability = prob_size;
        probability_copy = prob_size;
        mid_row = number_of_rows / 2;
        mid_col = number_of_columns / 2;
        double sum = 0.0;
        for (int i = 0; i < number_of_rows; i++) {
            for (int j = 0; j < number_of_columns; j++) {
                double distance_to_center = std::sqrt(
                    pow((abs(mid_row - i) * east_west_resolution), 2) +
                    pow((abs(mid_col - j) * north_south_resolution), 2));
                // determine probability based on distance
                if (kernel_type_ == DispersalKernelType::Cauchy) {
                    probability(i, j) = abs(cauchy.pdf(distance_to_center));
                }
                else if (kernel_type_ == DispersalKernelType::Exponential) {
                    probability(i, j) =
                        abs(exponential.pdf(distance_to_center));
                }
                sum += probability(i, j);
            }
        }
        // normalize based on the sum of all probabilities in the raster
        probability /= sum;
    }

    /*! Generates a new position for the spread.
     *
     *  Creates a copy of the probability matrix to mark where dispersers are
     * assigned. New window created any time a new cell is selected from
     * simulation.disperse
     *
     *  Selects next row/col value based on the cell with the highest
     * probability in the window.
     *
     */
    template <class Generator>
    std::tuple<int, int> operator()(Generator &generator, int row, int col)
    {
        UNUSED(generator); // Deterministic does not need random numbers.
        if (kernel_type_ != DispersalKernelType::Cauchy &&
            kernel_type_ != DispersalKernelType::Exponential) {
            throw std::invalid_argument("DeterministicDispersalKernel: "
                                        "Unsupported dispersal kernel type");
        }
        // reset the window if considering a new cell
        if (row != prev_row || col != prev_col) {
            proportion_of_dispersers = 1.0 / (double)dispersers_(row, col);
            probability_copy = probability;
        }

        int row_movement = 0;
        int col_movement = 0;

        double max = (double)-std::numeric_limits<int>::max();
        int max_prob_row = 0;
        int max_prob_col = 0;

        // find cell with highest probability
        for (int i = 0; i < number_of_rows; i++) {
            for (int j = 0; j < number_of_columns; j++) {
                if (probability_copy(i, j) > max) {
                    max = probability_copy(i, j);
                    max_prob_row = i;
                    max_prob_col = j;
                    row_movement = i - mid_row;
                    col_movement = j - mid_col;
                }
            }
        }

        // subtracting 1/number of dispersers ensures we always move the same
        // proportion of the individuals to each cell no matter how many are
        // dispersing
        probability_copy(max_prob_row, max_prob_col) -=
            proportion_of_dispersers;
        prev_row = row;
        prev_col = col;

        // return values in terms of actual location
        return std::make_tuple(row + row_movement, col + col_movement);
    }
};

} // namespace pops

#endif // POPS_DETERMINISTIC_KERNEL_HPP
