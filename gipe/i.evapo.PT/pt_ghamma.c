#include<stdio.h>
#include<math.h>
#include<stdlib.h>

//Prestely and Taylor, 1972. 

double pt_ghamma(double tempka, double patm_pt)
{
	double 	a, result;
	double Cp = 1004.16;

	if (tempka > 250.0){
		tempka = tempka - 273.15;
	}

	a = 0.622 * pow(10,7) * (2.501 - (2.361 * pow(10,-3) * tempka));

	result = Cp * patm_pt / a ;
	
	return result;
}

