#include <stdio.h>
#include <math.h>

double zom_0(double ndvi, double ndvi_max, double hv_ndvimax, double hv_desert)
{
    double a, b, z0m;

    /* hv_ndvimax = crop vegetation height (m) */
    /* hv_desert=0.002 = desert base vegetation height (m) */

    a = (log(hv_desert) -
         ((log(hv_ndvimax / 7) - log(hv_desert)) / (ndvi_max - 0.02) * 0.02));
    b = (log(hv_ndvimax / 7) - log(hv_desert)) / (ndvi_max - 0.02) * ndvi;
    z0m = exp(a + b);

    return (z0m);
}
