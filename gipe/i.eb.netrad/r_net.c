#include<stdio.h>
#include<math.h>
#include<stdlib.h>


#define PI 3.1415927

double r_net( double bbalb, double ndvi, double tempk, double dtair,  double e0, double tsw, double doy, double utc, double sunzangle )
{
	/* Tsw =  atmospheric transmissivity single-way (~0.7 -) */
	/* DOY = Day of Year */
	/* utc = UTC time of sat overpass*/
	/* sunzangle = sun zenith angle at sat. overpass */
	/* tair = air temperature (approximative, or met.station) */
	
	double 	Kin=0.0, Lin=0.0, Lout=0.0, Lcorr=0.0, result=0.0;
	double 	temp=0.0, ds=0.0, e_atm=0.0, delta=0.0;
	double	tsw_for_e_atm=0.7; //Special tsw, consider it a coefficient

// 	printf("**rnet: bbalb = %5.3f\n\tndvi = %5.3f\n\ttempk = %5.3f\n\te0 = %5.3f\n\ttsw = %5.3f\n\tdoy = %f\n\tutc = %5.3f\n\tsunzangle = %5.3f\n\tdtair = %5.3f\n",bbalb,ndvi,tempk,e0,tsw,doy,utc,sunzangle,dtair);
	
	// Atmospheric emissivity (Bastiaanssen, 1995)
	e_atm	=  1.08 * pow(-log(tsw_for_e_atm),0.265) ;
	// Atmospheric emissivity (Pawan, 2004)
// 	e_atm	= 0.85 * pow(-log(tsw),0.09);
// 	printf("rnet: e_atm = %5.3f\n",e_atm);

	ds = 1.0 + 0.01672 * sin(2*PI*(doy-93.5)/365);
// 	printf("rnet: ds = %lf\n",ds);
	delta = 0.4093*sin((2*PI*doy/365)-1.39);
// 	printf("rnet: delta = %5.3f\n",delta);
	
	// Kin is the shortwave incoming radiation
	Kin	= 1367.0 * (cos(sunzangle*PI/180) * tsw / (ds*ds) );
//  	printf("rnet: Kin = %5.3f\n",Kin);
	// Lin is incoming longwave radiation
	Lin	= (e_atm) * 5.67 * pow(10,-8) * pow((tempk-dtair),4);
//  	printf("rnet: Lin = %5.3f\n",Lin);
	// Lout is surface grey body emission in Longwave spectrum
	Lout	= e0 * 5.67 * pow(10,-8) * pow(tempk,4);
//  	printf("rnet: Lout = %5.3f\n",Lout);
	// Lcorr is outgoing longwave radiation "reflected" by the emissivity
	Lcorr	= (1.0 - e0) * Lin;
//  	printf("rnet: Lcorr = %5.3f\n",Lcorr);
	result	= (1.0 - bbalb) * Kin + Lin - Lout - Lcorr  ;
// 	printf("rnet: result = %5.3f\n",result);
	
	return result;
}

