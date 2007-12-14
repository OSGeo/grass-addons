#include<stdio.h>
#include<math.h>
#include"functions.h"

double roh_air_0(double tempk)
{
	double A, B, result;
	
	A = (24*(6.11*exp(17.27*36/(36+237.3)))/100.0);
	B = (24*(6.11*exp(17.27*36/(36+237.3)))/100.0);
	result = (1000.0 - A)/(tempk*2.87)+ B/(tempk*4.61);
	return result;
}

