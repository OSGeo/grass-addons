#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/config.h>


struct input
{
    char *name, *mapset;	/* input raster name  and mapset name */
    int infd;
    void *inrast;		/* input buffer */
};

void build_weight_vect(int nrows, int ncols, int ncriteria,
                       struct Option *weight, double *weight_vect);

void build_regime_matrix(int nrows, int ncols, int ncriteria,
                         double *weight_vect, double ***decision_vol);

