#include<stdio.h>
#include<math.h>
#include<stdlib.h>

#define PI 3.1415926
    
    /* Conversion of Radiance to Reflectance for Landsat 5TM */ 
double rad2ref_landsat5(double radiance, double doy, double sun_elevation,
			 double k_exo) 
{
    double result, ds;

    ds = (1 + 0.01672 * sin(2 * PI * (doy - 93.5) / 365));
    result =
	(radiance /
	 ((cos((90 - sun_elevation) * PI / 180) / (PI * ds * ds)) * k_exo));
    return result;
}


