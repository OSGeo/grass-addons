#include<stdio.h>
#include<math.h>

double h0(double roh_air, double cp, double rah, double dtair)
{
    double result;

    if (rah < 0.001) {
	result = -1.0;
    }
    else {
	result = roh_air * cp * dtair / rah;
    }

    return result;
}
