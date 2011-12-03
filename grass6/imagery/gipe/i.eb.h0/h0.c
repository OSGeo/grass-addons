#include<stdio.h>
#include<math.h>

double h0(double roh_air, double cp, double rah, double dtair)
{
    double result;

    result = roh_air * cp * dtair / rah;

    return result;
}
