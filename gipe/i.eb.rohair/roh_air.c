#include<stdio.h>
#include<stdlib.h>
#include<math.h>

/* Atmospheric Air Density 
 * Requires Air Temperature and DEM
 */

double roh_air(double dem, double tempka)
{
	double b, result;

	b = (( tempka - (0.00627 * dem )) / tempka );
	
	result = 349.467 * pow( b , 5.26 ) / tempka ;
		
	return result;
}
