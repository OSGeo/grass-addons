#include<stdio.h>
#include<math.h>

double mo_length(double roh_air, double cp, double ustar, double tempk,
		 double h0)
{
    double result;

    result = -roh_air * cp * pow(ustar, 3) * tempk / (0.41 * 9.81 * h0);

    return result;
}
