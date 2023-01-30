#include <stdio.h>
#include <math.h>
#include "functions.h"

double rohair(double dem, double tempk, double dtair)
{
    double a, b, result;

    a = tempk - dtair;
    b = ((a - 0.00627 * dem) / a);
    result = 349.467 * pow(b, 5.26) / a;

    return result;
}
