#include <stdio.h>
#include <math.h>
#include "functions.h"

#define PI 3.1415927

double rah1(double psih, double ustar)
{
    double result;

    result = (log10(2 / 0.01) - psih) / (ustar * 0.41);

    return (result);
}
