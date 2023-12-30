#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "functions.h"

double dt_air_desert(double h_desert, double roh_air_desert, double rah_desert)
{
    double result;

    result = (h_desert * rah_desert) / (roh_air_desert * 1004);
    return result;
}
