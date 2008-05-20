#include<stdio.h>
#include<math.h>
#include<stdlib.h>

//Prestely and Taylor, 1972. 

double pt_daily_et(double alpha_pt,double delta_pt,double ghamma_pt,double rnet,double g0,double tempka)
{
	double 	result, latentHv;
	double	roh_w=1004.15;//mass density of water
	double	vap_slope_ratio;

	/*Latent Heat of vaporization*/
	latentHv = (2.501-(0.002361*(tempka-273.15)))*1000000.0;

	/* Ratio of slope of saturation-vapour pressure Vs Temperature*/
	/* ghamma_pt = psychrometric constant */
	vap_slope_ratio = delta_pt / ( delta_pt + ghamma_pt );

	result = (alpha_pt/(roh_w*latentHv)) * vap_slope_ratio * (rnet-g0);
	
	return result;
}

