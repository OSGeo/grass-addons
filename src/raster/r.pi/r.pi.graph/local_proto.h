#ifndef LOCAL_PROTO_H
#define LOCAL_PROTO_H

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

typedef void(f_neighborhood)(DCELL max_dist, int fragcount);
typedef void(f_index)(DCELL *values, int fragcount);

/* func.c */
int get_dist_matrix(int fragcount);
void f_nearest_neighbor(DCELL max_dist, int fragcount);
void f_relative_neighbor(DCELL max_dist, int fragcount);
void f_gabriel(DCELL max_dist, int fragcount);
void f_spanning_tree(DCELL max_dist, int fragcount);

void f_connectance_index(DCELL *values, int fragcount);
void f_gyration_radius(DCELL *values, int fragcount);
void f_cohesion_index(DCELL *values, int fragcount);
void f_percent_patches(DCELL *values, int fragcount);
void f_percent_area(DCELL *values, int fragcount);
void f_number_patches(DCELL *values, int fragcount);
void f_number_links(DCELL *values, int fragcount);
void f_mean_patch_size(DCELL *values, int fragcount);
void f_largest_patch_size(DCELL *values, int fragcount);
void f_largest_patch_diameter(DCELL *values, int fragcount);
void f_graph_diameter_max(DCELL *values, int fragcount);

void FindClusters(int fragcount);

DCELL nearest_points(Coords **frags, int n1, int n2, Coords *np1, Coords *np2);

/* draw.c */
void flood_fill(int *map, int val, int x, int y, int sx, int sy);

/* hull.c */
void convex_hull(int *map, int nrows, int ncols);

/* global variables */
GLOBAL Coords *cells;
GLOBAL Coords **fragments;
GLOBAL DCELL *distmatrix;
GLOBAL int *adjmatrix;
GLOBAL int *patches;
GLOBAL int **clusters;
GLOBAL int clustercount;

#endif /* LOCAL_PROTO_H */
