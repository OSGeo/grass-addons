#include <stdio.h>
#include <math.h>
#include "functions.h"

double roh_air_0(double tempk)
{
    double A, B, result;

    A = (18 * (6.11 * exp(17.27 * 34.8 / (34.8 + 237.3))) / 100.0);
    B = (18 * (6.11 * exp(17.27 * 34.8 / (34.8 + 237.3))) / 100.0);
    result = (1000.0 - A) / (tempk * 2.87) + B / (tempk * 4.61);
    return result;
}
