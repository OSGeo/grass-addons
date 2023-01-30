#include <stdio.h>
#include <math.h>
#include "functions.h"

#define PI 3.1415927

double psi_h(double t0_dem, double h, double U_0, double roh_air)
{
    double result;

    double n5_temp, n11_mem, n12_mem;

    if (h != 0.0) {
        n5_temp = (-1004 * roh_air * pow(U_0, 3) * t0_dem) / (0.41 * 9.81 * h);
    }
    else {
        n5_temp = -1000.0;
    }

    if (n5_temp < 0.0) {
        n12_mem = pow((1 - 16 * (2 / n5_temp)), 0.25);
        n11_mem = (2 * log10((1 + pow(n12_mem, 2)) / 2));
    }
    else {
        n12_mem = 1.0;
        n11_mem = -5 * 2 / n5_temp;
    }

    result = n11_mem;

    return (result);
}
