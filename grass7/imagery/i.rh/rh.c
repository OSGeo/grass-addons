#include<stdio.h>
#include<math.h>

double rh(double PW,double Pa,double Ta,double dem){
	/*
	https{//www.researchgate.net/publication/227247013_High-resolution_Surface_Relative_Humidity_Computation_Using_MODIS_Image_in_Peninsular_Malaysia/
	PW <- MOD05_L2 product
	Pa <- MOD07 product
	Pa <- 1013.3-0.1038*dem
	Ta <- MOD07 product
	Ta <- -0.0065*dem+TaMOD07 (if dem>400m)
	
	https{//ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD05_L2/
	https{//ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD07_L2/
	*/
	/*Specific Humidity*/
	q=0.001*(-0.0762*PW*PW+1.753*PW+12.405);
	ta=-0.0065*dem+Ta;
	a=17.2694*ta/(ta+238.3);
	return(q*Pa/(380*exp(a)));
}

double esat(double tamean){
	/*
	esat{ saturated vapour pressure
	tamean{ air temperature daily mean
	*/
	return(610.78*exp(17.2694*tamean/(tamean+238.3));
}
double eact(double esat,double rh){
	/*
	eact{ actual vapour pressure
	esat{ saturated vapour pressure
	rh{ relative humidity
	*/
	return(0.01*esat*rh);
}
