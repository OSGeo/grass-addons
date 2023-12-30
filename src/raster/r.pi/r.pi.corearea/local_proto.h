#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
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
    double x, y;
} Vector2;

typedef struct {
    Position *positions;
    Position **borders;
    int count;
} PatchBorderList;

typedef DCELL(f_statmethod)(DCELL *, int);
typedef DCELL(f_propmethod)(DCELL, DCELL);

/* func.c */
void find_borders(int *flagbuf, int nrows, int ncols, int fragcount);
void init_border_values(double distance, double angle, int buffer,
                        f_statmethod stat, double dist_weight, int nrows,
                        int ncols, int fragcount);
void propagate(int neighbor_count, f_propmethod prop_method, int nrows,
               int ncols, int fragcount);

/* prop_method.c */
DCELL linear(DCELL value, DCELL propcost);
DCELL exponential(DCELL value, DCELL propcost);

/* global variables */
GLOBAL Coords *cells;
GLOBAL Coords **fragments;
GLOBAL DCELL *map;
GLOBAL DCELL *valmap;
GLOBAL DCELL *propmap;
GLOBAL PatchBorderList *patch_borders;

#endif /* LOCAL_PROTO_H */
