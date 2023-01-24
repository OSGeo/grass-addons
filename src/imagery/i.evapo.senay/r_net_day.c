#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Average Diurnal Net Radiation after Bastiaanssen (1995) */
double r_net_day(double bbalb, double solar, double tsw)
{
    double result;

    result = ((1.0 - bbalb) * solar) - (110.0 * tsw);
    return result;
}
