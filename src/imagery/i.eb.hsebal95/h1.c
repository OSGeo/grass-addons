#include <stdio.h>
#include <math.h>
#include "functions.h"

double h1(double roh_air, double rah, double dtair)
{
    double result;

    result = roh_air * 1004 * dtair / rah;

    return result;
}
