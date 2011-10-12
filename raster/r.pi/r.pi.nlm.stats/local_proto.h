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

#define TYPE_NOTHING 0
#define TYPE_NOGO -1

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
} Point;

typedef DCELL(*f_statmethod) (DCELL *, int);
typedef int (*f_func) (DCELL *, Coords **, int);

/* helpers.c */
int Round(double d);
int Random(int max);
double Randomf();
void print_buffer(int *buffer, int sx, int sy);
void print_map(double *map, int size);

/* func.c */
void FractalIter(double *map, double d, double dmod, int n, int size);
double DownSample(double *map, int x, int y, int newcols, int newrows,
		  int oldsize);
double CutValues(double *map, double mapcover, int size);
double UpSample(int *map, int x, int y, int oldcols, int oldrows,
		int newsize);
void MinMax(double *map, double *min, double *max, int size);

/* stat_method.c */
DCELL average(DCELL * vals, int count);
DCELL variance(DCELL * vals, int count);
DCELL mode(DCELL * vals, int count);
DCELL median(DCELL * vals, int count);
DCELL min(DCELL * vals, int count);
DCELL max(DCELL * vals, int count);

/* method.c */
int f_nearest_dist(DCELL * vals, Coords ** frags, int count);
int f_area(DCELL * vals, Coords ** frags, int count);
int f_perim(DCELL * vals, Coords ** frags, int count);
int f_shapeindex(DCELL * vals, Coords ** frags, int count);
int f_frac_dim(DCELL * vals, Coords ** frags, int count);

/* fractal.c */
void create_map(int *res);

/* frag.c */
/* writes one fragment */
void writeFragments(int *flagbuf, int nrows, int ncols, int nbr_cnt);

/* global parameters */
GLOBAL int verbose;
GLOBAL int *buffer;
GLOBAL double *bigbuf;
GLOBAL double landcover;
GLOBAL int sx, sy;
GLOBAL int power, size;
GLOBAL double sharpness;

GLOBAL Coords **fragments;
GLOBAL Coords *cells;
GLOBAL int fragcount;

#endif /* LOCAL_PROTO_H */
