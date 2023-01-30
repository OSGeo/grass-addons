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

typedef struct {
    Coords *first_cell;
    int count;
} Patch;

typedef struct {
    int *first_patch;
    int count;
} Cluster;

typedef void(f_neighborhood)(int *adjacency_matrix, DCELL *distmatrix,
                             int fragcount, DCELL max_dist);
typedef void(f_index)(DCELL *values, Cluster *cluster_list, int clustercount,
                      int *adjacency_matrix, Patch *fragments, int fragcount,
                      DCELL *distmatrix);
typedef DCELL(f_statmethod)(DCELL *vals, int count);

/* frag.c */
int writeFragments_local(Patch *fragments, int *flagbuf, int nrows, int ncols,
                         int nbr_cnt);

/* func.c */
int get_dist_matrix(DCELL *distmatrix, Patch *fragments, int fragcount);

void f_nearest_neighbor(int *adjacency_matrix, DCELL *distmatrix, int fragcount,
                        DCELL max_dist);
void f_relative_neighbor(int *adjacency_matrix, DCELL *distmatrix,
                         int fragcount, DCELL max_dist);
void f_gabriel(int *adjacency_matrix, DCELL *distmatrix, int fragcount,
               DCELL max_dist);
void f_spanning_tree(int *adjacency_matrix, DCELL *distmatrix, int fragcount,
                     DCELL max_dist);

void f_connectance_index(DCELL *values, Cluster *cluster_list,
                         int cluster_count, int *adjacency_matrix,
                         Patch *fragments, int fragcount, DCELL *distmatrix);
void f_gyration_radius(DCELL *values, Cluster *cluster_list, int cluster_count,
                       int *adjacency_matrix, Patch *fragments, int fragcount,
                       DCELL *distmatrix);
void f_cohesion_index(DCELL *values, Cluster *cluster_list, int cluster_count,
                      int *adjacency_matrix, Patch *fragments, int fragcount,
                      DCELL *distmatrix);
void f_percent_patches(DCELL *values, Cluster *cluster_list, int cluster_count,
                       int *adjacency_matrix, Patch *fragments, int fragcount,
                       DCELL *distmatrix);
void f_percent_area(DCELL *values, Cluster *cluster_list, int cluster_count,
                    int *adjacency_matrix, Patch *fragments, int fragcount,
                    DCELL *distmatrix);
void f_number_patches(DCELL *values, Cluster *cluster_list, int cluster_count,
                      int *adjacency_matrix, Patch *fragments, int fragcount,
                      DCELL *distmatrix);
void f_number_links(DCELL *values, Cluster *cluster_list, int cluster_count,
                    int *adjacency_matrix, Patch *fragments, int fragcount,
                    DCELL *distmatrix);
void f_mean_patch_size(DCELL *values, Cluster *cluster_list, int cluster_count,
                       int *adjacency_matrix, Patch *fragments, int fragcount,
                       DCELL *distmatrix);
void f_largest_patch_size(DCELL *values, Cluster *cluster_list,
                          int cluster_count, int *adjacency_matrix,
                          Patch *fragments, int fragcount, DCELL *distmatrix);
void f_largest_patch_diameter(DCELL *values, Cluster *cluster_list,
                              int cluster_count, int *adjacency_matrix,
                              Patch *fragments, int fragcount,
                              DCELL *distmatrix);
void f_graph_diameter_max(DCELL *values, Cluster *cluster_list,
                          int cluster_count, int *adjacency_matrix,
                          Patch *fragments, int fragcount, DCELL *distmatrix);

int find_clusters(Cluster *cluster_list, int *adjacency_matrix, int fragcount);

DCELL nearest_points(Patch *frags, int n1, int n2, Coords *np1, Coords *np2);
/* draw.c */
void draw_line(int *map, int val, int x1, int y1, int x2, int y2, int sx,
               int sy, int width);

#endif /* LOCAL_PROTO_H */
