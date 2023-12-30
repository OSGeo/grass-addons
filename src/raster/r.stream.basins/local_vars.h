#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/glocale.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/dbmi.h>

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

typedef struct {
    int r, c;
    int val;
} OUTLET;

typedef struct {
    int r, c;
} POINT;

GLOBAL int nextr[9];
GLOBAL int nextc[9];

GLOBAL OUTLET *outlets;
GLOBAL OUTLET *border_outlets;
GLOBAL int *categories;
GLOBAL int nrows, ncols;
GLOBAL int fifo_max;
GLOBAL POINT *fifo_points;
