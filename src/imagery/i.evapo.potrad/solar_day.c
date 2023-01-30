#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Average Solar Diurnal Radiation after Bastiaanssen (1995) */

#define PI 3.1415927
double solar_day(double lat, double doy, double tsw)
{
    double ws, cosun, latrad, deltarad, ds, result;

    /*Sun-Earth Distance (ds; A.U.) */
    ds = 1.0 + 0.01672 * sin(2 * PI * (doy - 93.5) / 365.0);

    /*Solar declination (delta; radians) */
    deltarad = 0.4093 * sin((2 * PI * doy / 365) - 1.39);

    /*Convert latitude in radians */
    latrad = lat * PI / 180.0;

    /*Convert latitude in radians */
    ws = acos(-tan(latrad) * tan(deltarad));
    cosun = ws * sin(deltarad) * sin(latrad) +
            cos(deltarad) * cos(latrad) * sin(ws);
    result = (cosun * 1367 * tsw) / (PI * ds * ds);
    return result;
}
