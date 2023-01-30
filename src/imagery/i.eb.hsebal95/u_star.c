#include <stdio.h>
#include <math.h>
#include "functions.h"

#define PI 3.1415927

double u_star(double t0_dem, double h, double ustar, double roh_air, double zom,
              double u2m)
{
    double result;

    double n5_temp; /* Monin-Obukov Length          */

    double n10_mem; /* psi m                        */

    double n31_mem; /* x for U200 (that is bh...)   */

    double hv = 0.15; /* crop height (m)              */

    double bh = 200; /* blending height (m)          */

    if (h != 0.0) {
        n5_temp =
            (-1004 * roh_air * pow(ustar, 3) * t0_dem) / (0.41 * 9.81 * h);
    }
    else {
        n5_temp = -1000.0;
    }

    if (n5_temp < 0.0) {

        n31_mem = pow((1 - 16 * (200 / n5_temp)), 0.25);
        n10_mem =
            (2 * log10((1 + n31_mem) / 2) + log10((1 + pow(n31_mem, 2)) / 2) -
             2 * atan(n31_mem) + 0.5 * PI);
    }
    else {

        /*              n31_mem = 1.0; */
        n10_mem = -5 * 2 / n5_temp;
    }

    result = ((u2m * 0.41 / log10(2 / (hv / 7))) / 0.41 *
              log10(bh / (hv / 7) * 0.41)) /
             (log10(bh / zom) - n10_mem);

    return (result);
}
