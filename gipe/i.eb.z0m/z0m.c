#include<stdio.h>
#include<stdlib.h>
#include<math.h>

/* Momentum roughness length (z0m) as seen in Pawan (2004) */

double z_0m(double sa_vi)
{
    double result;

    result = exp(-5.809 + 5.62 * sa_vi);

    return result;
}
