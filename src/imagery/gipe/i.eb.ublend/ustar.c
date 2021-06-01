#include<stdio.h>
#include<stdlib.h>
#include<math.h>


double u_star(double ublend, double hblend, double disp, double z0m,
	      double psim)
{
    double ustar;

    ustar = 0.41 * ublend / (log((hblend - disp) / z0m) - psim);

    return ustar;
}
