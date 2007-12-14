#include<stdio.h>
#include<math.h>
#include"functions.h"

double U_0(double zom_0, double u2m)
{
	double u_0;

	u_0 = u2m*0.41*log(200/(0.15/7))/(log(2/(0.15/7))*log(200/zom_0)); 

//	printf("u_0 = %5.3f\n", u_0);
	
	return (u_0);
}

