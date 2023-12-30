#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Average Diurnal Potential ET after Bastiaanssen (1995) */
double et_pot_day(double rnetd, double tempk, double roh_w)
{
    double latent, result;

    latent = (2.501 - (0.002361 * (tempk - 273.15))) * 1000000.0;
    result = (rnetd * 24.0 * 60.0 * 60.0 / 1000.0) / (latent * roh_w);
    return result;
}
