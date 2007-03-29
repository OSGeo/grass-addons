#include<stdio.h>
#include<math.h>
#include<stdlib.h>

//Prestely and Taylor, 1972. 

double pt_daily_et(double alpha_pt,double delta_pt,double ghamma_pt,double rnet,double g0)
{
	double 	result;
	
	result = (alpha_pt/28.588) * ( delta_pt / ( delta_pt + ghamma_pt ) ) * ( rnet - g0 ) ;
	
	return result;
}

