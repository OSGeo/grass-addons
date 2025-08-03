#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
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

typedef DCELL(f_statmethod)(DCELL *, int);
typedef int(f_func)(DCELL *, int, int *, int, f_statmethod);

DCELL value(DCELL *vals, int count);

int get_dist_matrix(int count);

int get_nearest_indices(int count, int *num_array, int num_count);

int f_dist(DCELL *, int, int *, int, f_statmethod);
int f_area(DCELL *, int, int *, int, f_statmethod);
int f_perim(DCELL *, int, int *, int, f_statmethod);
int f_shapeindex(DCELL *, int, int *, int, f_statmethod);
int f_path_dist(DCELL *, int, int *, int, f_statmethod);

int parseToken(int *res, int pos, char *token);

/* matrix.c */
int writeDistMatrixAndID(char *name, Coords **frags, int count);
int writeAdjacencyMatrix(char *name, Coords **frags, int count, int *nns,
                         int nn_count);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords **fragments;
GLOBAL int *flagbuf;
GLOBAL Coords *actpos;
GLOBAL DCELL *distmatrix;
GLOBAL int *nearest_indices;
GLOBAL int patch_n;

#endif /* LOCAL_PROTO_H */
