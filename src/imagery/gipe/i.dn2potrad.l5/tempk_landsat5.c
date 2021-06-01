#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /*
     * Surface temperature for Landsat 5TM 
     * Schneider and Mauser, 1996
     */ 
double tempk_landsat5(double l6) 
{
    double result;

    result = 1260.56 / (log((607.76 / (l6)) + 1.0));
    return result;
}


