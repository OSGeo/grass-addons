#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Chen et al., 2005. IJRS 26(8):1755-1762.
     * Estimation of daily evapotranspiration using a two-layer remote sensing model.
     */ 
double h_v(double tempk_g, double tempk_v, double tempk_a, double r_g,
	    double r_v, double r_a) 
{
    double a, b, c, result;

    a = r_g * tempk_v - r_g * tempk_a + r_v * tempk_g - r_v * tempk_a;
    b = r_v * r_g + r_g * r_a + r_v * r_a;
    c = r_a * (a / b);
    result = (tempk_v - c - tempk_a) / r_v;
    return result;
}


