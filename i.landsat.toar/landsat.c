#include<stdio.h>
#include<stdlib.h>
#include<math.h>

#define PI   3.1415926535897932384626433832795
#define R2D 57.295779513082320877
#define D2R  0.017453292519943295769

/****************************************************************************
 * PURPOSE: Calibrated digital number to Radiance
 *****************************************************************************/
double lsat_qcal2rad(int qcal, double lmax, double lmin, double qcalmax, double qcalmin)
{
    double gain, bias;

    gain = ((lmax - lmin) / (qcalmax - qcalmin));
    bias = lmin - gain * qcalmin;

    return (double)(((double)qcal) * gain + bias);
}

/****************************************************************************
 * PURPOSE: Radiance of non-thermal band to TOA Reflectance
 *****************************************************************************/
double lsat_rad2ref(double rad, double dist_es, double sun_elev, double esun)
{
    double a, b;

    a = PI * dist_es * dist_es;
    b = esun * cos((90 - sun_elev) * D2R);

    return (double)((rad * a) / b);
}

double lsat_refrad_ratio(double dist_es, double sun_elev, double esun)
{
    double a, b;

    a = PI * dist_es * dist_es;
    b = esun * cos((90 - sun_elev) * D2R);

    return (double)(a / b);
}

/****************************************************************************
 * PURPOSE: Radiance of thermal band to Kinetic Temperature
 *****************************************************************************/
double lsat_rad2temp(double rad, double K1, double K2)
{
    return (double)(K2 / log((K1 / rad) + 1.0) - 273.15);
}

/****************************************************************************
 * PUPOSE: Calibrated digital number of Landsat 5 to TOA Reflectance
 *****************************************************************************
double lsat_qcal2ref_tm5(int qcal, int band)
{
    static const double slope[] =
	{ 0.9398, 1.7731, 1.5348, 1.4239, 0.9828, 0., 1.3017 };
    static const double inter[] =
	{ 4.2934, 4.7289, 3.9796, 7.0320, 7.0185, 0., 7.6568 };

    static const double gain[] =
	{ 0.7756863, 0.7956862, 0.6192157, 0.6372549, 0.1257255, 0., 0.0437255 };
    static const double bias[] =
	{ -6.1999969, -6.3999939, -5.0000000, -5.1000061, -0.9999981, 0., -0.3500004 };

    --band;
    return (gain[band] * ((double)(qcal) * slope[band] + inter[band]) +
	    bias[band]);
}
*/
