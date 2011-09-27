#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

#define MAX_DOUBLE 1000000.0

typedef struct
{
    int x, y;
    int neighbors;
} Coords;

typedef DCELL(*f_func) (DCELL * values, int count);

/* frag.c */
void writeFrag(int row, int col, int nbr_cnt);

/* func.c */
void compute_values(DCELL * vals, int min, int max, f_func stat_method);

/* stat_method.c */
DCELL average(DCELL * vals, int count);
DCELL variance(DCELL * vals, int count);
DCELL mode(DCELL * vals, int count);
DCELL median(DCELL * vals, int count);
DCELL min(DCELL * vals, int count);
DCELL max(DCELL * vals, int count);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords **fragments;
GLOBAL int fragcount;
GLOBAL int *flagbuf;
GLOBAL DCELL *valsbuf;
GLOBAL Coords *actpos;
GLOBAL int cnt;
