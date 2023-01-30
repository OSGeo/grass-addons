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
    double dir;
    DCELL energy;
    int finished;
    int immigrated;
    int last_cat;
    int lost;
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
void perform_search(int *map, DCELL *costmap, int n, int fragcount, int sx,
                    int sy);

/* parameters */
GLOBAL int keyval;
GLOBAL double energy;
GLOBAL double percent;
GLOBAL int step_length;
GLOBAL int out_freq;
GLOBAL int perception_range;
GLOBAL double multiplicator;
GLOBAL int setback;
GLOBAL double step_range;

/* more global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

GLOBAL Individual *indi_array;
GLOBAL int *immigrants;
GLOBAL int *migrants;
GLOBAL int *emigrants;
GLOBAL int
    *patch_registry; /* ( patch1(indi1, indi2, ...), patch2(...), ... ) */
GLOBAL int *lost;
GLOBAL int *migrants_succ;
GLOBAL int *immi_matrix;
GLOBAL int *mig_matrix;

GLOBAL char *newname;
GLOBAL char outname[GNAME_MAX];

#endif /* LOCAL_PROTO_H */
