#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Evaporative fraction from Senay (2007) */
double evapfr_senay(double t_hot, double t_cold, double tempk)
{
    double result;

    result = (t_hot - tempk) / (t_hot - t_cold);
    return result;
}
