#ifndef __LOCAL_PROTO__
#define __LOCAL_PROTO__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <pcl/point_cloud.h>
#include <pcl/kdtree/impl/kdtree_flann.hpp>

extern "C" {
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/la.h>
#include <grass/glocale.h>
} // end extern "C"

#include <iostream>
#include <vector>

#ifndef MAX
#define MIN(a,b)      ((a<b) ? a : b)
#define MAX(a,b)      ((a>b) ? a : b)
#endif

#ifndef PI
#define PI M_PI
#endif

struct points
{
  int n;
  double *r;  // xyz
  double *r_min; // min coords 
  double *r_max; // max coords 
};

struct nna_par
{
  int i3;  // TRUE = 3D NNA, FALSE = 2D NNA (user sets by flag) 
  char v3; // TRUE = 3D layer, FALSE = 2D layer (according to Vect_is_3d()) 
  char *zcol; // not NULL if 3D NNA using 2D layer is required
};

struct convex
{
  int n; // number of hull vertices 
  int n_faces; // number of hull faces 
  int *hull;
  double *coord; // coordinates of faces 
  double *faces; // coordinates of vertices 
};

struct nearest
{
  double A;
  double rho;
  double rA;
  double rE;
  double R;
  double c;
};

extern "C" {
  double *get_col_values(struct Map_info *, int, const char *);
  void read_points(struct Map_info *, int, struct nna_par *, const char *, struct points *);
  double *triple(double, double, double);
  
  double bearing(double, double, double, double);
  double distance(double, double);
  int convexHull(struct points *, struct convex *);
  int make3DHull(struct points *, struct convex *);
  void convexHull3d(struct points *, struct convex *);
  double MBR(struct points *);
  double MBB(struct points *);
  int nn_average_distance_real(struct points *, struct nearest *);
  void density(struct points *, struct nna_par *, const char *, struct nearest *);
  void nn_average_distance_expected(struct nna_par *, struct nearest *);
  void nn_results(struct points *, struct nna_par *, struct nearest *);
  void nn_statistics(struct points *, struct nna_par *, struct nearest *);
} // end extern "C"
#endif
