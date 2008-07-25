#include<stdio.h>
#include<math.h>

// hu = height of measurement of wind speed
// u_hu = wind speed at hu height
// This is a meteorological area, standard grass height
// Used for initialization of wind speed

double U_0(double zom_0, double u_hu, double hu)
{
	double u_0;
	double grass_height=0.15; /* in meters */
	double hblend=200.0; /* blending height */
	u_0 = u_hu*0.41*log(hblend/(grass_height/7))/(log(hu/(grass_height/7))*log(hblend/zom_0)); 
//	printf("u_0 = %5.3f\n", u_0);
	return u_0;
}

