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

typedef DCELL(f_func) (DCELL * values, int count);

/* frag.c */
void writeFrag(int row, int col, int nbr_cnt);

/* func.c */
void compute_values(DCELL * vals, int min, int max, f_func stat_method);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords **fragments;
GLOBAL int fragcount;
GLOBAL int *flagbuf;
GLOBAL DCELL *valsbuf;
GLOBAL Coords *actpos;
GLOBAL int cnt;
