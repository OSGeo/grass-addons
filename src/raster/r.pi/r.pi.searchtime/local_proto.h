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

void print_buffer(int *buffer, int sx, int sy);
void print_d_buffer(DCELL *buffer, int sx, int sy);
void print_map(double *map, int size);
void print_array(DCELL *buffer, int size);
void print_fragments();

/* search.c */
void perform_search(DCELL *values, int *map, DCELL *costmap,
                    f_statmethod **stats, int stat_count, int n, int fragcount,
                    int sx, int sy);

/* indices.c */
DCELL shannon_index(int patch);
DCELL simpson_index(int patch);

/* global parameters */
GLOBAL int keyval;
GLOBAL double percent;
GLOBAL int maxsteps;
GLOBAL int step_length;
GLOBAL int out_freq;
GLOBAL int include_cost;
GLOBAL int perception_range;
GLOBAL double step_range;
GLOBAL double multiplicator;

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

GLOBAL Individual *indi_array;
GLOBAL int *patch_imi;

GLOBAL char *newname;
GLOBAL char *iminame;
GLOBAL const char *imimapset;

GLOBAL int *immi_matrix, *mig_matrix;

#endif /* LOCAL_PROTO_H */
