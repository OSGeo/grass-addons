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
    int patch;
} PatchPoint;

typedef DCELL(f_statmethod)(DCELL *, int);

/* frag.c */
int writeFragments_DCELL(DCELL *flagbuf, int nrows, int ncols, int nbr_cnt);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;
GLOBAL int sx, sy;
GLOBAL int *id_map;

GLOBAL int *adj_matrix;

#endif /* LOCAL_PROTO_H */
