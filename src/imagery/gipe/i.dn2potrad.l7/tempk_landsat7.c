#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Surface temperature for Landsat 7ETM+ */ 
double tempk_landsat7(double l6) 
{
    double result;

    result = 1282.71 / (log((666.09 / (l6)) + 1.0));
    return result;
}


