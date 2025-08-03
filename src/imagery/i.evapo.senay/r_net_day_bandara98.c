#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Average Diurnal Net Radiation after Bandara (1998) */
double r_net_day_bandara98(double surface_albedo, double solar_day,
                           double apparent_atm_emissivity,
                           double surface_emissivity, double air_temperature)
{
    double longwave_balance, result;

    double sigma = 5.67 * pow(10, -8); /*Stefann-Boltzmann Constant */

    longwave_balance = (apparent_atm_emissivity - surface_emissivity) * sigma *
                       pow(air_temperature, 4);
    result = ((1.0 - surface_albedo) * solar_day) - longwave_balance;
    return result;
}
