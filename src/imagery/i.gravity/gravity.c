#include <stdio.h>
#include <math.h>

/*# International Gravity Formula (For Latitude correction)*/
double g_lambda(double lambda)
{
    /*International Gravity Formula (mGal)
    lambda=latitude (dd)*/
    return (978031.8 * (1 + 0.0053024 * sin(lambda) * sin(lambda) -
                        0.0000059 * sin(2 * lambda) * sin(2 * lambda)));
}

/*# Eotvos Correction*/
double delta_g_eotvos(double alpha, double lambda, double v)
{
    /* Eotvos correction (mGal)
    v=velocity (kph)
    lambda=latitude (dd)
    alpha=direction of travel measured clockwise from North*/
    return (4.040 * v * sin(alpha) * cos(lambda) + 0.001211 * v * v);
}

/*# Free air Correction*/
double free_air(h)
{
    /* Free air Correction (mGal)
    h=height (m)*/
    return (0.3086 * h);
}

/*# Bouguer Correction*/
double delta_g_bouguer(double rho, double h)
{
    /* Bouguer Correction (mGal)
    G=gravity constant 6.67398 × 10^-11 [m3 kg-1 s-2]
    rho=density of slab (Mg/m3)
    h=height (m)*/
    return (2 * M_PI * 6.67398 * pow(10, -11) * rho * h);
}

double bouguer_anomaly(double g_obs, double freeair_corr, double bouguer_corr,
                       double terrain_corr, double latitude_corr,
                       double eotvos_corr)
{
    /*
    bouguer anomaly
    g_obs=observed gravity
    freeair_corr=free air correction
    bouguer_corr=bouguer correction
    terrain_corr=terrain correction
    latitude_corr=latitude correction
    eotvos_corr=eotvos correction
    */
    return (g_obs + freeair_corr - bouguer_corr + terrain_corr - latitude_corr +
            eotvos_corr);
}
