#include<stdio.h>
#include<math.h>

double evap_fr(double r_net, double g0, double h0)
{
    double result;

    result = (r_net - g0 - h0) / (r_net - g0);

    return result;
}
