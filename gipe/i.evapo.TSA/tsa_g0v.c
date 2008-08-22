#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Chen et al., 2005. IJRS 26(8):1755-1762.
     * estimation of daily evapotranspiration using a two-layer remote sensing model.
     */ 
double g_0v(double bbalb, double ndvi, double tempk_v, double rnet) 
{
    double a, b, result;

    a = (0.0032 * bbalb) + (bbalb * bbalb);
    b = (1 - 0.978 * pow(ndvi, 4));
    result = (rnet * (tempk_v - 273.15) / bbalb) * a * b;
    return result;
}


