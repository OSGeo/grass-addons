#include<stdio.h>
#include<stdlib.h>
#include<math.h>

//Wind speed at blending height

double u_blend(double u_hmoment, double disp,double hblend,double z0m, double hmoment){
	double ublend;
	
	ublend=u_hmoment*(log10(hblend-disp)-log10(z0m))/(log10(hmoment-disp)-log10(z0m));

	return ublend;
}
