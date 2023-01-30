/*
 * PoPS model - Various statistics computation
 *
 * Copyright (C) 2015-2020 by the authors.
 *
 * Authors: Anna Petrasova <akratoc gmail com>
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_STATISTICS_HPP
#define POPS_STATISTICS_HPP

namespace pops {

/**
 * Computes sum of infected hosts
 * from all cells of a raster.
 */
template <typename IntegerRaster>
unsigned sum_of_infected(const IntegerRaster &infected)
{
    unsigned sum = 0;
    for (int j = 0; j < infected.rows(); j++) {
        for (int k = 0; k < infected.cols(); k++) {
            sum += infected(j, k);
        }
    }
    return sum;
}
/**
 * Computes infected area as number
 * of cell > 0 times cell size.
 */
template <typename IntegerRaster>
double area_of_infected(const IntegerRaster &infected, double ew_res,
                        double ns_res)
{
    unsigned cells = 0;
    for (int j = 0; j < infected.rows(); j++) {
        for (int k = 0; k < infected.cols(); k++) {
            if (infected(j, k) > 0)
                cells++;
        }
    }
    return cells * ew_res * ns_res;
}

} // namespace pops
#endif // POPS_STATISTICS_HPP
