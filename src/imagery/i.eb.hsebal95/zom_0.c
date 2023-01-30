#include <stdio.h>
#include <math.h>
#include "functions.h"

double zom_0(double ndvi, double ndvi_max)
{
    double a, b, zom;

    double hv_ndvimax = 1.5; /* crop vegetation height (m) */

    double hv_desert = 0.002; /* desert base vegetation height (m) */

    a = (log(hv_desert) -
         ((log(hv_ndvimax / 7) - log(hv_desert)) / (ndvi_max - 0.02) * 0.02));
    b = ((log(hv_ndvimax / 7) - log(hv_desert)) / (ndvi_max - 0.02)) * ndvi;
    zom = exp(a + b);
    /* Greece works and SEBAL01 */
    /*zom = exp(3.3219*ndvi-3.9939); */
    return (zom);
}
