#include <stdio.h>
#include <math.h>
#include "functions.h"

#define PI 3.1415927

double psi_m(double t0_dem, double h, double ustar, double roh_air, double hu)
{
    double result;

    double n5, n10, n12;

    if (h != 0.0) {
        n5 = (-1004 * roh_air * pow(ustar, 3) * t0_dem) / (0.41 * 9.81 * h);
    }
    else {
        n5 = -1000.0;
    }
    if (n5 < 0.0) {
        n12 = pow((1 - 16 * (hu / n5)), 0.25);
        n10 = (2 * log((1 + n12) / 2)) + log((1 + pow(n12, 2)) / 2) -
              2 * atan(n12) + 0.5 * PI;
    }
    else {
        n12 = 1.0;
        n10 = -5 * hu / n5;
    }
    result = n10;
    return (result);
}
