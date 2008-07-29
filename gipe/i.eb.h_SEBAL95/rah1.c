#include<stdio.h>
#include<math.h>
#include"functions.h"

double rah1(double zom_0, double psih, double psim, double ustar)
{
	double  u5, result;
	u5 = (ustar/0.41)*log(5/zom_0);
	result = (1.0/(u5*pow(0.41,2)))*(log(5/zom_0)-psim)*(log(5/(zom_0*0.1))-psih);
	return result;
}

