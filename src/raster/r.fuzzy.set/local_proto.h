#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <grass/raster.h>
#include <grass/gis.h>
#include <grass/glocale.h>
/*
   PI2= PI/2
   PI4= PI/4
 */
#ifndef PI2
#define PI2 (2 * atan(1))
#endif

#ifndef PI4
#define PI4 (atan(1))
#endif

#define LINEAR 0
#define SSHAPE 1
#define JSHAPE 2
#define GSHAPE 3

#define BOTH   0
#define LEFT   1
#define RIGHT  2

extern char *input, *output;
extern float shape, height;
extern int type, side;
extern double p[4]; /* inflection points */
extern int num_points;

float fuzzy(FCELL cell);
