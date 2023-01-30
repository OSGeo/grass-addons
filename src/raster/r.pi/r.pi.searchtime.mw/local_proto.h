#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include <grass/gis.h>
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
    double dir;
    DCELL path;
    int finished;
} Individual;

typedef struct {
    int x, y;
    double dir;
    double weight;
} WeightedCoords;

typedef struct {
    int x, y;
} Displacement;

typedef DCELL(f_statmethod)(DCELL *, int);

/* search.c */
void perform_search(DCELL *values, int *map, DCELL *costmap, int size,
                    f_statmethod **stats, int stat_count, int n, int fragcount,
                    int sx, int sy);

/* global parameters */
GLOBAL double percent;
GLOBAL int maxsteps;
GLOBAL int step_length;
GLOBAL int out_freq;
GLOBAL int include_cost;
GLOBAL int perception_range;
GLOBAL double multiplicator;

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

GLOBAL Individual *indi_array;
GLOBAL int *patch_imi;

#endif /* LOCAL_PROTO_H */
