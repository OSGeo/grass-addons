#include <stdio.h>
#include <math.h>
#include "functions.h"

double U_0(double zom_0, double u2m)
{
    double u_0;

    u_0 = u2m * 0.41 * log10(200 / (0.15 / 7)) /
          (log10(2 / (0.15 / 7)) * log10(200 / zom_0));

    return (u_0);
}
