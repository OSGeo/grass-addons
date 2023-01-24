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

typedef struct {
    int x, y;
} Point;

typedef DCELL(f_statmethod)(DCELL *, int);
typedef void(f_func)(DCELL *, Coords **, int, f_statmethod);

/* func.c */
void f_distance(DCELL *vals, Coords **frags, int count,
                f_statmethod statmethod);
void f_area(DCELL *vals, Coords **frags, int count, f_statmethod statmethod);

/* global parameters */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

#endif /* LOCAL_PROTO_H */
