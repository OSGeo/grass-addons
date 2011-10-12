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

#define TYPE_NOTHING -1

#define RESOLUTION 10000

#define MIN_DOUBLE -1000000
#define MAX_DOUBLE 1000000

typedef struct
{
    int x, y;
    int neighbors;
    double value;
} Coords;

typedef struct
{
    int x, y;
    double dir;
    DCELL energy;
    int finished;
    int immigrated;
    int last_cat;
    int lost;
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

/* frag.c */
void writeFragments(int *flagbuf, int nrows, int ncols, int nbr_cnt);

/* search.c */
void perform_search(int *map, DCELL * costmap, DCELL * suitmap,
		    int remove_indi);

/* stat_method.c */
DCELL average(DCELL * vals, int count);
DCELL variance(DCELL * vals, int count);
DCELL std_deviat(DCELL * vals, int count);
DCELL median(DCELL * vals, int count);
DCELL min(DCELL * vals, int count);
DCELL max(DCELL * vals, int count);

/* parameters */
GLOBAL int sx, sy;
GLOBAL int keyval;
GLOBAL int n;
GLOBAL double energy;
GLOBAL double percent;
GLOBAL int step_length;
GLOBAL int out_freq;
GLOBAL int perception_range;
GLOBAL double multiplicator;
GLOBAL int setback;

/* more global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;
GLOBAL int fragcount;

GLOBAL Individual *indi_array;
GLOBAL int *immigrants;
GLOBAL int *migrants;
GLOBAL int *emigrants;
GLOBAL int *patch_registry;	// ( patch1(indi1, indi2, ...), patch2(...), ... )
GLOBAL int *lost;
GLOBAL int *migrants_succ;
GLOBAL char *deleted_arr;

GLOBAL char *newname, *newmapset;
GLOBAL char outname[GNAME_MAX];


#endif /* LOCAL_PROTO_H */
