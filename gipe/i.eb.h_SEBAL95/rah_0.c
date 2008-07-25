#include<stdio.h>
#include<math.h>
#include"functions.h"

double rah_0(double zom_0, double u_hu, double hu)
{
	double ustar, u5, result;
	ustar = (u_hu*0.41)/(log(hu/zom_0));
	u5 = (ustar/0.41)*log(5/zom_0);
	result = (1/(pow(u5*0.41,2))) * log(5/zom_0) * log(5/(zom_0*0.1));
	return result;
}

