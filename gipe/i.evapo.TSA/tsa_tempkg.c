#include<stdio.h>
#include<math.h>
#include<stdlib.h>
 
    /* Temperature of ground from Tvegetation
     * Based on two sources pixel split
     * Chen et al., 2005. IJRS 26(8):1755-1762.
     * Estimation of daily evapotranspiration using a two-layer remote sensing model.
     */ 
double tempk_g(double tempk, double tempk_v, double fv) 
{
    double result;

    result = (tempk - (fv * tempk_v)) / (1 - fv);
    return result;
}


