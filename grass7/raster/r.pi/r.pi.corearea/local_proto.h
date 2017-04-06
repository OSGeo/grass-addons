#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "../r.pi.library/r_pi.h"

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

typedef struct
{
    int x, y;
} Position;

typedef struct
{
    double x, y;
} Vector2;

typedef struct
{
    Position *positions;
    Position **borders;
    int count;
} PatchBorderList;

typedef DCELL(f_statmethod) (DCELL *, int);
typedef DCELL(f_propmethod) (DCELL, DCELL);

/* frag.c */
void writeFragments(int *flagbuf, int nrows, int ncols, int nbr_cnt);

/* func.c */
void find_borders(int *flagbuf);
void init_border_values(double distance, double angle, int buffer,
			f_statmethod stat, double dist_weight);
void propagate(int neighbor_count, f_propmethod prop_method);

/* prop_method.c */
DCELL linear(DCELL value, DCELL propcost);
DCELL exponential(DCELL value, DCELL propcost);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords *cells;
GLOBAL Coords **fragments;
GLOBAL int fragcount;
GLOBAL int *flagbuf;
GLOBAL DCELL *map;
GLOBAL DCELL *valmap;
GLOBAL DCELL *propmap;
GLOBAL PatchBorderList *patch_borders;

#endif /* LOCAL_PROTO_H */
