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
} Point;

typedef DCELL(f_statmethod)(DCELL *, int);
typedef int(f_func)(DCELL *, Coords **, int);

void print_buffer(int *buffer, int sx, int sy);
void print_map(double *map, int size);

/* func.c */
void FractalIter(double *map, double d, double dmod, int n, int size);
double DownSample(double *map, double min, int x, int y, int newcols,
                  int newrows, int oldsize);
double CutValues(double *map, double mapcover, int size);
double UpSample(int *map, int x, int y, int oldcols, int oldrows, int newsize);
void MinMax(double *map, double *min, double *max, int size);

/* method.c */
int f_nearest_dist(DCELL *vals, Coords **frags, int count);
int f_area(DCELL *vals, Coords **frags, int count);
int f_perim(DCELL *vals, Coords **frags, int count);
int f_shapeindex(DCELL *vals, Coords **frags, int count);
int f_frac_dim(DCELL *vals, Coords **frags, int count);

/* fractal.c */
void create_map(int *res, int size);

/* global parameters */
GLOBAL int *buffer;
GLOBAL double *bigbuf;
GLOBAL double landcover;
GLOBAL int sx, sy;
GLOBAL int power;
GLOBAL double sharpness;

GLOBAL Coords **fragments;
GLOBAL Coords *cells;

#endif /* LOCAL_PROTO_H */
