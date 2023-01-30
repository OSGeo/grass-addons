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

typedef int(f_method)(Position *, int, int, int *, int, int);

/* func.c */
int f_circular(Position *list, int count, int neighbors, int *flagbuf,
               int nrows, int ncols);
int f_random(Position *list, int count, int neighbors, int *flagbuf, int nrows,
             int ncols);
int f_costbased(Position *list, int count, int neighbors, int *flagbuf,
                int nrows, int ncols);
int gather_border(Position *res, int neighbors, int *flagbuf, int nrows,
                  int ncols);

/* global variables */
GLOBAL DCELL *costmap;

#endif /* LOCAL_PROTO_H */
