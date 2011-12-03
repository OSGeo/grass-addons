#include<stdio.h>
#include<stdlib.h>
#include<math.h>


double ra_h(double disp, double z0h, double psih, double ustar, double hu)
{
    double rah;

    rah = (log((hu - disp) / z0h) - psih) / (0.41 * ustar);

    return rah;
}
