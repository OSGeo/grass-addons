#include<stdio.h>
#include<math.h>
#include<stdlib.h>
 
    /* Temperature of vegetation
     * Based on two sources pixel split
     * Chen et al., 2005. IJRS 26(8):1755-1762.
     * Estimation of daily evapotranspiration using a two-layer remote sensing model.
     */ 
double tempk_v(double tempk, double fv) 
{
    double a, result;

    a =
	(fv -
	 (pow(fv, 0.5) * pow(0.97, 0.25))) / ((pow((1 - fv), 0.5) *
					       pow(0.93, 0.25)) - 1 - fv);
    result = tempk / (fv - (1 - fv) * a);
    return result;
}


