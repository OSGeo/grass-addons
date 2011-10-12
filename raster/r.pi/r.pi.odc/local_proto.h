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

#define NOGO -2
#define NOTHING -1

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

typedef struct
{
    int x, y;
    int patch;
} PatchPoint;

typedef DCELL(*f_statmethod) (DCELL *, int);
typedef DCELL(*f_compensate) (DCELL, int);

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

/* voronoi.c */
void voronoi(DCELL * values, int *map, int sx, int sy, int diag_move);
void calc_neighbors(DCELL * res, DCELL * focals, f_statmethod * methods,
		    int stat_count, f_compensate compensate,
		    int neighbor_level);
void getNeighborCount(DCELL * res);

/* stat_method.c */
DCELL average(DCELL * vals, int count);
DCELL variance(DCELL * vals, int count);
DCELL std_deviat(DCELL * vals, int count);
DCELL median(DCELL * vals, int count);

/* compensation.c */
DCELL none(DCELL value, int frag);
DCELL odd_area(DCELL value, int frag);
DCELL area_odd(DCELL value, int frag);
DCELL odd_perim(DCELL value, int frag);
DCELL perim_odd(DCELL value, int frag);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;
GLOBAL int fragcount;
GLOBAL int sx, sy;

GLOBAL int *adj_matrix;

GLOBAL int empty_count;

#endif /* LOCAL_PROTO_H */
