#include<stdio.h>
#include<stdlib.h>
#include<math.h>

#include "landsat.h"

#define PI   3.1415926535897932384626433832795
#define R2D 57.295779513082320877
#define D2R  0.017453292519943295769

/****************************************************************************
 * PURPOSE: Calibrated Digital Number to at-satellite Radiance
 *****************************************************************************/
double lsat_qcal2rad(int qcal, band_data * band)
{
    return (double)(((double)qcal) * band->gain + band->bias);
}

/****************************************************************************
 * PURPOSE: Radiance of non-thermal band to at-satellite Reflectance
 *****************************************************************************/
double lsat_rad2ref(double rad, band_data * band)
{
    return (double)(rad / band->K2);
}

/****************************************************************************
 * PURPOSE: Radiance of thermal band to at-satellite Temperature
 *****************************************************************************/
double lsat_rad2temp(double rad, band_data * band)
{
    return (double)(band->K2 / log((band->K1 / rad) + 1.0));
}

/****************************************************************************
 * PURPOSE: Some band constants
 *
 *      zenith = 90 - sun_elevation
 *      sin( sun_elevation ) = cos( sun_zenith )
 *
 *      lsat : satellite data
 *         i : band number
 *    method : level of atmospheric correction
 *       aot : atmospheric optical thickness (usually 0.15)
 *   percent : percent of solar irradiance in path radiance
 *****************************************************************************/

void lsat_bandctes(lsat_data * lsat, int i, char method, double aot, double percent)
{
    double a, b, rad_sun;
    double TAUv, TAUz, Edown;

    a = (double)(PI * lsat->dist_es * lsat->dist_es);
    b = (double)(sin(D2R * lsat->sun_elev));

    /** Radiance of the Sun */
    if (method == SIMPLIFIED) {
        TAUv = 1.;      /* TAUv  = at. transmittance surface-sensor */
                        /* TAUz  = at. transmittance sun-surface    */
        TAUz = (lsat->band[i].wavemax < 1.) ? b : 1.;
        Edown = 0.;     /* Edown = diffuse sky spectral irradiance  */
    }
    else { /* UNCORRECTED or CORRECTED */
        TAUv = 1.;
        TAUz = 1.;
        Edown   = 0.;
    }
    rad_sun = ((lsat->band[i].esun * b * TAUz + Edown) / a);

    /** Radiance coefficients */
    lsat->band[i].gain = ((lsat->band[i].lmax - lsat->band[i].lmin) /
                          (lsat->band[i].qcalmax - lsat->band[i].qcalmin));
    lsat->band[i].bias = (lsat->band[i].lmin -
                          lsat->band[i].gain * lsat->band[i].qcalmin);

    if (method == CORRECTED)
    {
        lsat->band[i].bias -= lsat->band[i].lmin;
    }
    else if (method == SIMPLIFIED)
    {
        lsat->band[i].gain /= TAUv;
        lsat->band[i].bias -= (lsat->band[i].lmin - percent * rad_sun);
        lsat->band[i].bias /= TAUv;
    }

    /** Reflectance coefficients, only NO thermal bands.
        Same variables are utilized to thermal constants
     */
    if (lsat->band[i].thermal == 0)
    {
        lsat->band[i].K1 = 0.;
        lsat->band[i].K2 = rad_sun;
    }
}

