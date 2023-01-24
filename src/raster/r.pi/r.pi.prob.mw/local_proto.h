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

typedef DCELL(f_statmethod)(DCELL *, int);

void print_buffer(int *buffer, int sx, int sy);
void print_d_buffer(DCELL *buffer, int sx, int sy);
void print_map(double *map, int size);
void print_array(DCELL *buffer, int size);
void print_fragments();

/* analysis.c */
void perform_analysis(DCELL *values, int *map, int *mask, int n, int size,
                      int patch_only, int sx, int sy);

/* frag.c*/
int writeFragments_dist(int *flagbuf, int nrows, int ncols, double distance);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;

#endif /* LOCAL_PROTO_H */
