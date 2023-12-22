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

typedef struct {
    int x, y;
    int patch;
} PatchPoint;

typedef DCELL(f_statmethod)(DCELL *, int);
typedef DCELL(f_compensate)(DCELL, int);

void print_buffer(int *buffer, int sx, int sy);
void print_d_buffer(DCELL *buffer, int sx, int sy);
void print_map(double *map, int size);
void print_array(DCELL *buffer, int size);
void print_fragments();

/* voronoi.c */
void voronoi(DCELL *values, int *map, int sx, int sy, int diag_move,
             int fragcount);
void calc_neighbors(DCELL *res, DCELL *focals, f_statmethod **methods,
                    int stat_count, f_compensate compensate, int neighbor_level,
                    int fragcount);
void getNeighborCount(DCELL *res, int fragcount);

/* compensation.c */
DCELL none(DCELL value, int frag);
DCELL odd_area(DCELL value, int frag);
DCELL area_odd(DCELL value, int frag);
DCELL odd_perim(DCELL value, int frag);
DCELL perim_odd(DCELL value, int frag);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

GLOBAL int *adj_matrix;

GLOBAL int empty_count;

#endif /* LOCAL_PROTO_H */
