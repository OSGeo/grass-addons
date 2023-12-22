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

/* func.c */
int f_proximity(DCELL *, Coords **, int, int, int);
int f_modified_prox(DCELL *vals, Coords **frags, int count, int min, int max);
int f_neighborhood(DCELL *, Coords **, int, int, int);

/* global variables */
GLOBAL Coords **fragments;
GLOBAL Coords *actpos;

#endif /* LOCAL_PROTO_H */
