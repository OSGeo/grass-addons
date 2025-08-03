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

typedef DCELL(f_func)(DCELL *values, int count);

/* func.c */
void compute_values(DCELL *vals, int fragcount, int min, int max,
                    f_func stat_method);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL DCELL *valsbuf;
GLOBAL Coords *actpos;
