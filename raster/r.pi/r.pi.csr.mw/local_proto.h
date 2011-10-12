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

typedef DCELL(*f_statmethod) (DCELL *, int);
typedef void (*f_method) (DCELL * values, int *map, int *mask, int n,
			  int size);

/* helpers.c */
int Round(double d);
int Random(int max);
double Randomf();
void print_buffer(int *buffer, int sx, int sy);
void print_d_buffer(DCELL * buffer, int sx, int sy);
void print_map(double *map, int size);
void print_array(DCELL * buffer, int size);
void print_fragments();

/* stat_method.c */
DCELL average(DCELL * vals, int count);
DCELL variance(DCELL * vals, int count);
DCELL std_deviat(DCELL * vals, int count);
DCELL median(DCELL * vals, int count);
DCELL min(DCELL * vals, int count);
DCELL max(DCELL * vals, int count);

/* analysis.c */
void clark_evans(DCELL * values, int *map, int *mask, int n, int size);
void donnelly(DCELL * values, int *map, int *mask, int n, int size);

/* global parameters */
GLOBAL int sx, sy;

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;
GLOBAL int fragcount;

#endif /* LOCAL_PROTO_H */
