#ifndef _LANDSAT_H
#define _LANDSAT_H

#define MAX_BANDS   9

/* Band data */
typedef struct
{
    int number;			/* Band number                   */
    int code;			/* Band code                     */
    double lmax, lmin;		/* Spectral radiance             */
    double qcalmax, qcalmin;	/* Quantized calibrated pixel    */
    double esun;		/* Solar espectral irradiance    */

} band_data;

/* Landsat data */
typedef struct
{
    char date[11];		/* Satelite image date           */
    double dist_es;		/* Distance Earth-Sun            */
    double sun_elev;		/* Solar elevation               */
    double K1, K2;		/* Thermal calibration constant  */
    int bands;			/* Total number of bands         */
    band_data band[MAX_BANDS];	/* Data for each band            */

} lsat_data;


/*****************************************************************************
 * Landsat Equations Prototypes
 *****************************************************************************/

double lsat_qcal2rad(int qcal, double lmax, double lmin, double qcalmax, double qcalmin);
double lsat_rad2ref(double rad, double dist_es, double sun_elev, double esun);
double lsat_refrad_ratio(double dist_es, double sun_elev, double esun);
double lsat_rad2temp(double rad, double K1, double K2);

#endif
