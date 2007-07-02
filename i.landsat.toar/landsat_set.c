#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "landsat.h"
#include "earth_sun.h"

#define MET_SIZE    5600	/* .met file size 5516 bytes */
#define MAX_STR      127

/* utility for read met file */
void get_value_met(char *mettext, char *text, char *value)
{
    char *ptr;

    ptr = strstr(mettext, text);
    if (ptr == NULL)
	return;

    while (*ptr++ != '=') ;
    sscanf(ptr, "%s", value);
    return;
}

/****************************************************************************
 * PURPOSE:     Read values of Landsat-7 ETM+ from header (.met) file
 *****************************************************************************/
void met_ETM(char *metfile, lsat_data * lsat)
{
    FILE *f;
    char mettext[MET_SIZE];
    char name[MAX_STR], value[MAX_STR];
    int i, j;

    static int band[] = { 1, 2, 3, 4, 5, 6, 6, 7, 8 };
    static int code[] = { 1, 2, 3, 4, 5, 61, 62, 7, 8 };

    static double esun[] =
	{ 1969., 1840., 1551., 1044., 225.7, 0., 82.07, 1368. };


    if ((f = fopen(metfile, "r")) == NULL) {
	G_fatal_error(_(".met file '%s' not found"), metfile);
    }
    fread(mettext, 1, MET_SIZE, f);

    get_value_met(mettext, "ACQUISITION_DATE", value);
    strncpy(lsat->date, value, 11);
    lsat->dist_es = earth_sun(lsat->date);

    get_value_met(mettext, "SUN_ELEVATION", value);
    lsat->sun_elev = atof(value);

    lsat->K1 = 666.09;
    lsat->K2 = 1282.71;

    lsat->bands = 9;
    for (i = 0; i < lsat->bands; i++) {
	lsat->band[i].number = *(band + i);
	lsat->band[i].code = *(code + i);
	lsat->band[i].esun = *(esun + lsat->band[i].number - 1);

	snprintf(name, MAX_STR, "LMAX_BAND%d", lsat->band[i].code);
	get_value_met(mettext, name, value);
	lsat->band[i].lmax = atof(value);
	snprintf(name, MAX_STR, "LMIN_BAND%d", lsat->band[i].code);
	get_value_met(mettext, name, value);
	lsat->band[i].lmin = atof(value);
	snprintf(name, MAX_STR, "QCALMAX_BAND%d", lsat->band[i].code);
	get_value_met(mettext, name, value);
	lsat->band[i].qcalmax = atof(value);
	snprintf(name, MAX_STR, "QCALMIN_BAND%d", lsat->band[i].code);
	get_value_met(mettext, name, value);
	lsat->band[i].qcalmin = atof(value);
    }

    (void)fclose(f);
    return;
}


/****************************************************************************
 * PURPOSE:     Store values of Landsat-4 TM
 *
 *              date: adquisition date of image
 *              elevation: solar elevation angle
 *****************************************************************************/
void set_TM4(lsat_data * lsat, char date[], double elevation)
{
    int i;

    static int band[] = { 1, 2, 3, 4, 5, 6, 7 };
    static double esun[] = { 1958., 1828., 1559., 1045., 219.1, 0., 74.57 };
    static double lmax[] = { 185., 342., 245., 270., 36., 0., 19. };
    static double lmin[] = { -1.5, -3.1, -2.7, -2.5, -0.45, 0., -0.3 };

    strncpy(lsat->date, date, 11);
    lsat->sun_elev = elevation;
    lsat->dist_es = earth_sun(lsat->date);

    lsat->K1 = 607.76;
    lsat->K2 = 1260.56;

    lsat->bands = 7;
    for (i = 0; i < lsat->bands; i++) {
	lsat->band[i].number = *(band + i);
	lsat->band[i].code = lsat->band[i].number;
	lsat->band[i].esun = *(esun + lsat->band[i].number - 1);
	lsat->band[i].lmax = *(lmax + lsat->band[i].number - 1);
	lsat->band[i].lmin = *(lmin + lsat->band[i].number - 1);
	lsat->band[i].qcalmax = 255.;
	lsat->band[i].qcalmin = 0.;
    }
    return;
}


/****************************************************************************
 * PURPOSE:     Store values of Landsat-5 TM
 *
 *              date: adquisition date of image
 *              elevation: solar elevation angle
 *              after: flag for processing date
 *****************************************************************************/
void set_TM5(lsat_data * lsat, char date[], double elevation, char after)
{
    int i;
    double *lmax, *lmin;

    static int band[] = { 1, 2, 3, 4, 5, 6, 7 };
    static double esun[] = { 1957., 1829., 1557., 1047., 219.3, 0., 74.52 };

    /* Spectral radiances at detecter before May 4, 2003 */
    static double lmaxb[] =
	{ 152.10, 296.81, 204.30, 206.20, 27.19, 15.303, 14.38 };
    static double lminb[] =
	{ -1.52, -2.84, -1.17, -1.51, -0.37, 1.2378, -0.15 };

    /* Spectral radiances at detecter after May 5, 2003 */
    static double lmaxa[] =
	{ 193.00, 365.00, 264.00, 221.00, 30.20, 15.303, 16.50 };
    static double lmina[] =
	{ -1.52, -2.84, -1.17, -1.51, -0.37, 1.2378, -0.15 };

    strncpy(lsat->date, date, 11);
    lsat->sun_elev = elevation;
    lsat->dist_es = earth_sun(lsat->date);

    lsat->K1 = 607.76;
    lsat->K2 = 1260.56;

    lsat->bands = 7;
    if (after != 0) {
	lmax = lmaxa;
	lmin = lmina;
    }
    else {
	lmax = lmaxb;
	lmin = lminb;
    }
    for (i = 0; i < lsat->bands; i++) {
	lsat->band[i].number = *(band + i);
	lsat->band[i].code = lsat->band[i].number;
	lsat->band[i].esun = *(esun + lsat->band[i].number - 1);
	lsat->band[i].lmax = *(lmax + lsat->band[i].number - 1);
	lsat->band[i].lmin = *(lmin + lsat->band[i].number - 1);
	lsat->band[i].qcalmax = 255.;
	lsat->band[i].qcalmin = 0.;
    }
    return;
}


/****************************************************************************
 * PURPOSE:     Store values of Landsat-7 ETM+
 *
 *              date: adquisition date of image
 *              elevation: solar elevation angle
 *              gain: nine H/L chars for band gain
 *              before: flag for processing date
 *****************************************************************************/
void set_ETM(lsat_data * lsat, char date[], double elevation, char gain[],
	     char before)
{
    int i;
    double *lmax, *lmin;

    static int band[] = { 1, 2, 3, 4, 5, 6, 6, 7, 8 };
    static int code[] = { 1, 2, 3, 4, 5, 61, 62, 7, 8 };

    static double esun[] =
	{ 1969., 1840., 1551., 1044., 225.7, 0., 82.07, 1368. };

    /* Spectral radiances at detector before July 1, 2000 */
    /*   Low gain */
    static double lmaxLb[] =
	{ 297.5, 303.4, 235.5, 235.0, 47.70, 17.04, 16.600, 244.0 };
    static double lminLb[] = { -6.2, -6.0, -4.5, -4.5, -1.0, 0.0, -0.35, -5.0 };
    /*   High gain */
    static double lmaxHb[] =
	{ 194.3, 202.4, 158.6, 157.5, 31.76, 12.65, 10.932, 158.4 };
    static double lminHb[] = { -6.2, -6.0, -4.5, -4.5, -1.0, 3.2, -0.35, -5.0 };

    /* Spectral radiances at detector after July 1, 2000 */
    /*   Low gain */
    static double lmaxLa[] =
	{ 293.7, 300.9, 234.4, 241.1, 47.57, 17.04, 16.540, 243.1 };
    static double lminLa[] = { -6.2, -6.4, -5.0, -5.1, -1.0, 0.0, -0.35, -4.7 };
    /*   High gain */
    static double lmaxHa[] =
	{ 191.6, 196.5, 152.9, 157.4, 31.06, 12.65, 10.800, 158.3 };
    static double lminHa[] = { -6.2, -6.4, -5.0, -5.1, -1.0, 3.2, -0.35, -4.7 };


    strncpy(lsat->date, date, 11);
    lsat->sun_elev = elevation;
    lsat->dist_es = earth_sun(lsat->date);

    lsat->K1 = 666.09;
    lsat->K2 = 1282.71;

    lsat->bands = 9;
    for (i = 0; i < lsat->bands; i++) {
	lsat->band[i].number = *(band + i);
	lsat->band[i].code = *(code + i);
	lsat->band[i].esun = *(esun + lsat->band[i].number - 1);
	lsat->band[i].qcalmax = 255.;
	lsat->band[i].qcalmin = 1.;
	if (before != 0) {
	    if (gain[i] == 'H' || gain[i] == 'h') {
		lmax = lmaxHb;
		lmin = lminHb;
	    }
	    else {
		lmax = lmaxLb;
		lmin = lminLb;
	    }
	}
	else {
	    if (gain[i] == 'H' || gain[i] == 'h') {
		lmax = lmaxHa;
		lmin = lminHa;
	    }
	    else {
		lmax = lmaxLa;
		lmin = lminLa;
	    }
	}
	lsat->band[i].lmax = *(lmax + lsat->band[i].number - 1);
	lsat->band[i].lmin = *(lmin + lsat->band[i].number - 1);
    }
    return;
}
