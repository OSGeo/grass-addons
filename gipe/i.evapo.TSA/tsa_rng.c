#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Chen et al., 2005. IJRS 26(8):1755-1762.
     * Estimation of daily evapotranspiration using a two-layer remote sensing model.
     */ 
double rn_g(double rnet, double fv) 
{
    double result;

    result = (1 - fv) * rnet;
    return result;
}


