#include<stdio.h>
#include<math.h>
#include"functions.h"

#define PI 3.1415927

double u_star(double t0_dem,double h,double ustar,double roh_air,double zom,double u_hu,double hu)
{
	double result;
	double n5; 	/* Monin-Obukov Length 		*/
        double n10; 	/* psi m 			*/
	double n31; 	/* x for U200 (that is bh...) 	*/
	double hv=0.15;	/* grass height (m) 		*/
	double bh=200;	/* blending height (m) 		*/
//	printf("t0dem = %5.3f\n", t0_dem);
//	printf("h = %5.3f\n", h);
//	printf("U_0 = %5.3f\n", U_0);
//	printf("roh_air = %5.3f\n", roh_air);
//	printf("zom = %5.3f\n", zom);
//	printf("u_hu = %5.3f\n", u_hu);
	if(h != 0.0){
		n5 = (-1004* roh_air*pow(ustar,3)* t0_dem)/(0.41*9.81* h);
	} else {
		n5 = -1000.0;
	}
	if(n5 < 0.0){
		n31 = pow((1-16*(hu/n5)),0.25);
		n10 = (2*log((1+n31)/2)+log((1+pow(n31,2))/2)-2*atan(n31)+0.5*PI);
	} else {
//		n31 = 1.0;
		n10 = -5*2/n5;
	}
	result = ((u_hu*0.41/log(hu/(hv/7)))/0.41*log(bh/(hv/7)*0.41))/(log(bh/zom)-n10);
	return result;
}

