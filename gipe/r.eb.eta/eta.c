#include<stdio.h>
#include<math.h>

double et_a(double r_net_day, double evap_fr, double tempk)
{
	double result;
	
	result = (r_net_day * evap_fr) * 86400/((2.501-0.002361*(tempk-273.15))*pow(10,6));
	
	return result;
}

