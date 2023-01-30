/*
 * Declarations for the whole module
 *
 * Authors:
 *   Bob Covill <bcovill tekmap.ns.ca>
 *   Vaclav Petras <wenzeslaus gmail com>
 *
 * Copyright 2000-2016 by Bob Covill, and the GRASS Development Team
 *
 * This program is free software licensed under the GPL (>=v2).
 * Read the COPYING file that comes with GRASS for details.
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/raster3d.h>

#include "double_list.h"

/* main.c */
int do_profile(double e1, double e2, double n1, double n2, int coords,
               double res, RASTER3D_Map *fd, int data_type, FILE *fp,
               char *null_string, const char *unit, double factor,
               RASTER3D_Region *region, int depth, struct DoubleList *values);

/* read_rast.c */
int read_rast(double east, double north, double dist, RASTER3D_Map *fd,
              int coords, RASTER_MAP_TYPE data_type, FILE *fp,
              char *null_string, RASTER3D_Region *region, int depth,
              struct DoubleList *values);

/* input.c */
int input(char *, char *, char *, char *, char *, FILE *);

extern int clr;
extern struct Colors colors;
