/*!
   \file random.c

   \brief Random number generation

   (C) 2020 by Anna Petrasova, Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
   \author Vaclav Petras
 */
#include <stdbool.h>
#include <math.h>

#include <grass/gis.h>

#include "random.h"

/*!
 * \brief Generates 2 numbers from normal distribution N(mean, std_dev)
 * using Marsaglia polar method.
 *
 * \param[in] mean
 * \param[in] std_dev
 * \param[out] x
 * \param[out] y
 */
void gauss_xy(double mean, double std_dev, double *x, double *y)
{
    double r = 0., vv1, vv2, fac;
    vv1 = vv2 = 0;

    while (r >= 1. || r == 0.) {
        vv1 = G_drand48() * 2. - 1.;
        vv2 = G_drand48() * 2. - 1.;
        r = vv1 * vv1 + vv2 * vv2;
    }
    fac = sqrt(log(r) * -2. / r);
    (*y) = mean + std_dev * vv1 * fac;
    (*x) = mean + std_dev * vv2 * fac;
}

/*!
 * \brief Initialize gauss generator structure
 * with distribution parameters N(mean, std_dev).
 */
void gauss_generator_init(struct GaussGenerator *generator, double mean,
                          double std_dev)
{
    generator->has_spare = false;
    generator->mean = mean;
    generator->std_dev = std_dev;
}

/*!
 * \brief Returns number from normal distribution N(mean, std_dev).
 * GaussGenerator structure needs to be initialezed first with
 * gauss_generator_init.
 *
 * \return random number
 */
double gauss_generator_next(struct GaussGenerator *generator)
{
    double x, y;

    if (generator->has_spare) {
        generator->has_spare = false;
        return generator->spare;
    }
    else {
        gauss_xy(generator->mean, generator->std_dev, &x, &y);
        generator->spare = y;
        generator->has_spare = true;
        return x;
    }
}
