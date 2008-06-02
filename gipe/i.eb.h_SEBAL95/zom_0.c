#include<stdio.h>
#include<math.h>
#include"functions.h"

double zom_0(double ndvi, double ndvi_max)
{
	double a, b, zom;
	double hv_ndvimax=1.5; /* crop vegetation height (m) */
	double hv_desert=0.002; /* desert base vegetation height (m) */
	
	a = (log10(hv_desert)-((log10(hv_ndvimax/7)-log10(hv_desert))/(ndvi_max-0.02)*0.02));
	b = (log10(hv_ndvimax/7)-log10(hv_desert))/(ndvi_max-0.02)* ndvi;
	zom = exp(a+b); 
	
//	printf("zom = %5.3f\n", zom);
	
	return (zom);
}

