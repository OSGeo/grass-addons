#include<stdio.h>
#include<math.h>
#include"functions.h"

/* Pixel-based input required are: tempk water & desert
 * additionally, dtair in Desert point should be given
 */ 


double dt_air(double t0_dem, double tempk_water, double tempk_desert, double dtair_desert)
{
	double a, b, result;
	
	a = (dtair_desert-0.0)/(tempk_desert-tempk_water);
	b = 0.0 - a * tempk_water;
	
	result = t0_dem * a + b;
	
	return result;
}

