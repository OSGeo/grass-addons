#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Average Diurnal Potential ET after Bastiaanssen (1995) */ 
double et_pot_day(double bbalb, double solar, double tempk, double tsw,
		   double roh_w) 
{
    double latent, result;

    latent = (2.501 - (0.002361 * (tempk - 273.15))) * 1000000.0;
    result =
	((((1.0 - bbalb) * solar) -
	  (110.0 * tsw)) * 86400 * 1000.0) / (latent * roh_w);
    return result;
}


