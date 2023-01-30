#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H
#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

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

/* parse.c */
void parse(DCELL *values, char *file_name, int id_col, int val_col,
           int fragcount);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *cells;
GLOBAL int *adj_matrix;

#endif /* LOCAL_PROTO_H */
