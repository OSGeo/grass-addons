#include <stdio.h>
#include <math.h>

double z0m_bastiaanssen(double ndvi, double ndvi_max, double hv_ndvimax,
                        double hv_desert)
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

/* Momentum roughness length (z0m) as seen in Pawan (2004) */
double z0m_pawan(double sa_vi)
{
    return (exp(-5.809 + 5.62 * sa_vi));
}
