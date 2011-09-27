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

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

#define TYPE_NOTHING -1

#define RESOLUTION 10000

#define MIN_DOUBLE -1000000
#define MAX_DOUBLE 1000000

typedef struct
{
    int x, y;
    int neighbors;
} Coords;

typedef struct
{
    int x, y;
    double dir;
    DCELL path;
    int finished;
} Individual;

typedef struct
{
    int x, y;
    double dir;
    double weight;
} WeightedCoords;

typedef struct
{
    int x, y;
} Displacement;

typedef DCELL(*f_statmethod) (DCELL *, int);

/* helpers.c */
int Round(double d);
int Random(int max);
double Randomf();
void print_buffer(int *buffer, int sx, int sy);
void print_d_buffer(DCELL * buffer, int sx, int sy);
void print_map(double *map, int size);
void print_array(DCELL * buffer, int size);
void print_fragments();

/* frag.c */
void writeFragments(int *flagbuf, int nrows, int ncols, int nbr_cnt);

/* stat_method.c */
DCELL average(DCELL * vals, int count);
DCELL variance(DCELL * vals, int count);
DCELL std_deviat(DCELL * vals, int count);
DCELL median(DCELL * vals, int count);
DCELL min(DCELL * vals, int count);
DCELL max(DCELL * vals, int count);

/* search.c */
void perform_search(DCELL * values, int *map, DCELL * costmap, int size,
		    f_statmethod * stats, int stat_count);

/* global parameters */
GLOBAL int sx, sy;
GLOBAL int n;
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
GLOBAL int fragcount;

GLOBAL Individual *indi_array;
GLOBAL int *patch_imi;


#endif /* LOCAL_PROTO_H */
