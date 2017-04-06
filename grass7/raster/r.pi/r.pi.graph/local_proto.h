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

typedef struct
{
    int x, y;
} Position;

typedef void (f_neighborhood) (DCELL max_dist);
typedef void (f_index) ();

/* frag.c */
void writeFragments(int *flagbuf, int nrows, int ncols, int nbr_cnt);

/* func.c */
int get_dist_matrix();
void f_nearest_neighbor(DCELL max_dist);
void f_relative_neighbor(DCELL max_dist);
void f_gabriel(DCELL max_dist);
void f_spanning_tree(DCELL max_dist);

void f_connectance_index(DCELL * values);
void f_gyration_radius(DCELL * values);
void f_cohesion_index(DCELL * values);
void f_percent_patches(DCELL * values);
void f_percent_area(DCELL * values);
void f_number_patches(DCELL * values);
void f_number_links(DCELL * values);
void f_mean_patch_size(DCELL * values);
void f_largest_patch_size(DCELL * values);
void f_largest_patch_diameter(DCELL * values);
void f_graph_diameter_max(DCELL * values);

void FindClusters();

DCELL nearest_points(Coords ** frags, int n1, int n2, Coords * np1,
		     Coords * np2);

/* draw.c */
void draw_line(int *map, int val, int x1, int y1, int x2, int y2, int sx,
	       int sy, int width);
void flood_fill(int *map, int val, int x, int y, int sx, int sy);

/* hull.c */
void convex_hull(int *map);

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL Coords *cells;
GLOBAL Coords **fragments;
GLOBAL int fragcount;
GLOBAL int *flagbuf;
GLOBAL DCELL *distmatrix;
GLOBAL int *adjmatrix;
GLOBAL int *patches;
GLOBAL int **clusters;
GLOBAL int clustercount;

#endif /* LOCAL_PROTO_H */
