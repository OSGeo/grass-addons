#ifndef __LOCAL_PROTO__
#define __LOCAL_PROTO__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>

#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include <grass/rtree.h>

#include "hull.h"

#ifndef MAX
#define MIN(a, b) ((a < b) ? a : b)
#define MAX(a, b) ((a > b) ? a : b)
#endif

#ifndef PI
#define PI M_PI
#endif

struct points {
    int n;                // # of input points
    double *r;            // coordinates of input points
    struct RTree *R_tree; // spatial index
    double *r_min;        // minimum coordinates
    double *r_max;        // maximum coordinates
    double max_dist;      // maximum distance
};

struct nna_par {
    int i3;     // true = 3D NNA, false = 2D NNA (user sets by flag)
    char v3;    // true = 3D layer, false = 2D layer (according to Vect_is_3d())
    char *zcol; // not NULL if 3D NNA using 2D layer is required
};

struct convex {
    int n;       // # of hull vertices
    int n_faces; // # of hull faces
    int *hull;
    double *coord; // coordinates of faces
    double *faces; // coordinates of vertices
};

struct nearest {
    double A;   // area/volume for density of input points calculation
    double rho; // density of the input points
    double rA;  // real average distance of the NN
    double rE;  // expected average distance of the NN
    double R;   // ratio of real and expected average distance of the NN
    double c;   // test statistics
};

double *get_col_values(struct Map_info *, int, const char *);
void read_points(struct Map_info *, int, struct nna_par *, const char *,
                 struct points *);
double *triple(double, double, double);

struct RTree *create_spatial_index(struct nna_par *);
void insert_rectangle(int, int, struct points *);
struct ilist *spatial_search(int, int, struct points *, double);
struct ilist *find_NNs(int, int, struct points *);
double sum_NN(int, int, struct ilist *, struct points *);

double bearing(double, double, double, double);
double distance(double, double);
int cmpVals(const void *, const void *);
int convexHull(struct points *, struct convex *);
int make3DHull(struct points *, struct convex *);
void convexHull3d(struct points *, struct convex *);
double MBR(struct points *);
double MBB(struct points *);
void nn_average_distance_real(struct nna_par *, struct points *,
                              struct nearest *);
void density(struct points *, struct nna_par *, const char *, struct nearest *);
void nn_average_distance_expected(struct nna_par *, struct nearest *);
void nn_results(struct points *, struct nna_par *, struct nearest *);
void nn_statistics(struct points *, struct nna_par *, struct nearest *);
#endif
