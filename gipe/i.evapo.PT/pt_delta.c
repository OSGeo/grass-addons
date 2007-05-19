#include<stdio.h>
#include<math.h>
#include<stdlib.h>

//Prestely and Taylor, 1972. 

double pt_delta(double tempka)
{
	double 	a, b, result;
	
	if (tempka > 250.0){
		tempka = tempka - 273.15;
	}
	a = ( 17.27 * tempka ) / ( 237.3 + tempka ) ;
	b = tempka + 237.3 ;

	result = 2504 * exp(a) / pow(b,2) ;
	
	return result;
}

