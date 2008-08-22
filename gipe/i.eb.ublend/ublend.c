#include<stdio.h>
#include<stdlib.h>
#include<math.h>

/*Wind speed at blending height */

double u_blend(double u_hmoment, double disp, double hblend, double z0m,
	       double hmoment)
{
    double ublend;

    ublend =
	u_hmoment * (log(hblend - disp) - log(z0m)) / (log(hmoment - disp) -
						       log(z0m));

    return ublend;
}
