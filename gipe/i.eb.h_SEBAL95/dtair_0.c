#include<stdio.h>
#include<math.h>
#include"functions.h"

/* Pixel-based input required are: tempk water & desert
 * additionally, dtair in Desert is vaguely initialized
 */ 
#define ZERO 273.15

double dt_air_0(double t0_dem, double tempk_water, double tempk_desert)
{
	double a, b, result;
	double dtair_desert_0;
	
	if(tempk_desert > (ZERO+48.0)){
		dtair_desert_0 = 13.0;
	} else if(tempk_desert >= (ZERO+40.0) && tempk_desert < (ZERO+48.0)){
		dtair_desert_0 = 10.0;
	} else if(tempk_desert >= (ZERO+32.0) && tempk_desert < (ZERO+40.0)){
		dtair_desert_0 = 7.0;
	} else if(tempk_desert >= (ZERO+25.0) && tempk_desert < (ZERO+32.0)){
		dtair_desert_0 = 5.0;
	} else if(tempk_desert >= (ZERO+18.0) && tempk_desert < (ZERO+25.0)){
		dtair_desert_0 = 3.0;
	} else if(tempk_desert >= (ZERO+11.0) && tempk_desert < (ZERO+18.0)){
		dtair_desert_0 = 1.0;
	} else {
		dtair_desert_0 = 0.0;
//		printf("WARNING!!! dtair_desert_0 is NOT VALID!\n");
	}

//	printf("dtair0 = %.0f K\t",dtair_desert_0);
	
	a = (dtair_desert_0-0.0)/(tempk_desert-tempk_water);
	b = 0.0 - a * tempk_water;
	
//	printf("dt_air_0(a) = %5.3f Tempk(b) %5.3f\n",a,b);	
	
	result = t0_dem * a + b;
//	printf("dt_air_0 = %5.3f\n",result);	
	
	return result;
}

