#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "../r.pi.library/r_pi.h"

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

typedef DCELL(f_statmethod)(DCELL *, int);
typedef void(f_method)(DCELL *values, int *map, int *mask, int n, int size);

/* analysis.c */
void clark_evans(DCELL *values, int *map, int *mask, int n, int size);
void donnelly(DCELL *values, int *map, int *mask, int n, int size);

/* global parameters */
GLOBAL int sx, sy;

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

#endif /* LOCAL_PROTO_H */
