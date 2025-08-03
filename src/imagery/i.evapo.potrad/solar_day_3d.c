#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Average Solar Diurnal Radiation after Bastiaanssen (1995)
 * Includes Slope and aspect correction
 */

#define PI 3.1415927
double solar_day_3d(double lat, double doy, double tsw, double slope,
                    double aspect)
{
    double ws, costheta, latrad, delta, deltarad, ds, result;

    double temp1, temp2, temp3, temp4, temp5;

    double slrad, asprad; /*slope and aspect in radians */

    ds = 1.0 + 0.01672 * sin(2 * PI * (doy - 93.5) / 365.0);
    delta = 0.4093 * sin((2 * PI * doy / 365) - 1.39);
    deltarad = delta * PI / 180.0;
    latrad = lat * PI / 180.0;
    slrad = slope * PI / 180.0;
    asprad = aspect * PI / 180.0;
    ws = acos(-tan(latrad) * tan(deltarad));
    temp1 = sin(deltarad) * sin(latrad) * cos(slrad);
    temp2 = sin(deltarad) * cos(latrad) * sin(slrad) * cos(asprad);
    temp3 = cos(deltarad) * cos(latrad) * cos(slrad) * cos(ws * PI / 180.0);
    temp4 = cos(deltarad) * sin(slrad) * cos(asprad) * cos(ws * PI / 180.0);
    temp5 = cos(deltarad) * sin(slrad) * sin(asprad) * sin(ws * PI / 180.0);
    costheta = (temp1 - temp2 + temp3 + temp4 + temp5) / cos(slrad);
    result = (costheta * 1367 * tsw) / (PI * ds * ds);
    return result;
}
