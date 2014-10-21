#ifndef __LOCAL_PROTO__
#define __LOCAL_PROTO__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <pcl/point_types.h>
#include <pcl/io/pcd_io.h>
#include <pcl/point_cloud.h>
#include <pcl/kdtree/impl/kdtree_flann.hpp>

extern "C" {
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/la.h>
#include <grass/raster3d.h>
#include <grass/glocale.h>
}

#ifndef PI
#define PI M_PI
#endif

#ifndef SQUARE
#define SQUARE(a)      (a*a)
#define POW3(a)        (a*a*a)
#define POW4(a)        (a*a*a*a)
#endif

struct opts
{
  struct Option *input, *output, *phase, *report, *crossvalid, *function_var_hz, *function_var_vert, *function_var_final, *form_file, *field, *intpl, *zcol, *var_dir_hz, *var_dir_vert, *nL, *nZ, *td_hz, *td_vert, *nugget_hz, *nugget_vert, *nugget_final, *sill_hz, *sill_vert, *sill_final, *range_hz, *range_vert, *range_final;
};

struct flgs
{
  struct Flag *d23; /* 2D/3D interpolation */
  struct Flag *bivariate;
  struct Flag *univariate;
  struct Flag *detrend;
};

struct select
{
  int n;     // # of selected
  int out;   // # of the others
  int total; // total number
  int *indices; // indices of selected
};

struct points // inputs
{
  int n; // number of points 
  double *r; // triples of coordinates (e.g. x0 y0 z0... xn yn zn)
  double *r_min; // min coords 
  double *r_max; // max coords 
  double center[3]; // center
  double *invals; // values to be interpolated
  struct select in_reg; // points in region
  mat_struct *trend;
};

struct pcl_utils
{
  pcl::PointCloud<pcl::PointXYZ>::Ptr pnts;
  pcl::KdTreeFLANN<pcl::PointXYZ>::Ptr kd_tree;

  pcl::PointCloud<pcl::PointXYZ>::Ptr pnts_hz;
  pcl::KdTreeFLANN<pcl::PointXYZ>::Ptr kd_tree_A;

  pcl::PointCloud<pcl::PointXYZ>::Ptr pnts_vert;
  pcl::KdTreeFLANN<pcl::PointXYZ>::Ptr kd_tree_xy;
};

struct bivar
{
  int vert;
  char *variogram;
  int function;
  double sill;
  double nugget;
  double h_range;  
};

struct parameters
{
  int function;
  int type;
  int const_val;
  double dir;
  double td;  // range of directions 

  double radius;      // radius
  double max_dist;    // maximum distance
  double max_dist_vert;

  int nLag;       // number of length pieces 
  double lag;   // maximum distance between nearest neighbours (variogram lag)

  int nLag_vert;
  double lag_vert;

  double *h;    // horizontal intervals used to estimate experimental variogram 
  double *vert; // vertical intervals used to estimate experimental variogram 
  mat_struct *c; // number of elements in each lag (final variogram only)
  mat_struct *gamma; // value of experimental variogram
  double nugget;
  double sill;
  double part_sill;
  double h_range;

  struct bivar horizontal;
  struct bivar vertical;

  mat_struct *A;
  mat_struct *T;   // coefficients of theoretical variogram
  mat_struct *GM; // matrix of diffences between point values based on the distances and the theoretical variogram

  char *name;  // name of input vector layer 
  char term[12]; // output format - gnuplot terminal 
  char ext[4]; // output format - file format
};

struct var_par // parameters of experimental variogram 
{
  struct parameters hz;
  struct parameters vert;
  struct parameters fin;

  //double Lmax;   // maximal length in horizontal direction 
  //double dzmax;  // maximal elevation difference 
  //double radius; // radius for kd-tree 
};

struct write
{
  int write2file; // write to file or not
  char *name; // filename
  FILE *fp;
  time_t now;
};

struct int_par // Interpolation settings 
{
  int i3; // TRUE = 3D interpolation, FALSE = 2D interpolation (user sets by flag) 
  char v3; // TRUE = 3D layer, FALSE = 2D layer (according to Vect_is_3d()) 
  int phase;
  int bivar;
  int univar;
  double aniso_ratio;
  int const_val;
  struct write report;
  struct write crossvalid;
};

extern "C" {
  struct reg_par // Region settings -> output extent and resolution 
  {
    struct Cell_head reg_2d; // region for 2D interpolation 
    RASTER3D_Region reg_3d;  // region for 3D interpolation 
    double west;			// region.west 
    double east;
    double north;			// region.north 
    double south;
    double bot;			// region.bottom 
    double top;
    double ew_res;		// east-west resolution 
    double ns_res;		// north-south resolution 
    double bt_res;		// bottom-top resolution 
    int nrows;			// number of rows 
    int ncols;			// number of cols 
    int ndeps;			// number of deps 
    int nrcd;
  };

  struct output
  {
    DCELL *dcell;
    int fd_2d;
    RASTER3D_Map *fd_3d;
    char *name;		// name of output 2D/3D raster 
  };
}

double *get_col_values(struct Map_info *, struct int_par *, struct points *, int, const char *, int);
void test_normality(int , double *, struct write *);
void read_points(struct Map_info *, struct reg_par *, struct points *, struct pcl_utils *, struct int_par, const char *, int, struct write *);
double min(double *, struct points *);
double max(double *, struct points *);

void coord_diff(int, int, double *, double *);
double distance_diff(double *);
double radius_hz_diff(double *);
double *triple(double, double, double);
double lag_distance(int, struct points *, pcl::PointCloud<pcl::PointXYZ>::Ptr, struct parameters *, struct write *);
int lag_number(double, double *);
void variogram_restricts(struct int_par *, struct points *, pcl::PointCloud<pcl::PointXYZ>::Ptr, struct parameters *);
void geometric_anisotropy(struct int_par *, struct points *, pcl::PointCloud<pcl::PointXYZ>::Ptr);
double find_intersect_x(double *, double *, double *, double *, struct write *);
double find_intersect_y(double *, double *, double *, double *, double , struct write *);
mat_struct *LSM(mat_struct *, mat_struct *);
mat_struct *nonlin_LMS(int , double *, double *);
void E_variogram(int, struct int_par *, struct points *, struct pcl_utils *, struct var_par *);
void T_variogram(int, struct opts, struct parameters *, struct write *);
void ordinary_kriging(struct int_par *, struct reg_par *, struct points *, struct pcl_utils *, struct var_par *, struct output *);

int set_function(char *, struct parameters *, struct write *);
double RBF(double *);
double linear(double, double, double);
double exponential(double, double, double, double);
double spherical(double, double, double, double);
double gaussian(double, double, double, double);
double variogram_fction(struct parameters *, double *);
void set_gnuplot(char *, struct parameters *);
void plot_experimental_variogram(struct int_par *, double *, mat_struct *, struct parameters *);
void plot_var(int, double *, mat_struct *, struct parameters *);
void variogram_type(int, char *);
void write2file_basics(struct int_par *, struct opts *);
void write2file_vector(struct int_par *, struct points *);
void write2file_values(struct write *, const char *);
void write2file_varSetsIntro(int, struct write *);
void write2file_varSets(struct write *, struct parameters *);
void write2file_variogram_E(struct int_par *, struct parameters *);
void write2file_variogram_T(struct write *);
void write_temporary2file(struct int_par *, struct parameters *, mat_struct *);
void read_tmp_vals(const char *, struct parameters *, struct int_par *);
  
mat_struct *set_up_G(struct points *, struct parameters *, struct write *);
mat_struct *set_up_g0(struct int_par *, std::vector<int>, struct points *, double *, struct parameters *);
mat_struct *submatrix(std::vector<int> , mat_struct *, struct write *);
double result(std::vector<int>, struct points *, mat_struct *);

void crossvalidation(struct int_par *, struct points *, pcl::PointCloud<pcl::PointXYZ>::Ptr, struct parameters *);
void cell_centre(unsigned int, unsigned int, unsigned int, struct int_par *, struct reg_par *, double *, struct parameters *);

extern "C" {
void get_region_pars(struct int_par *, struct reg_par *);
void open_layer(struct int_par *, struct reg_par *, struct output *);
int write2layer(struct int_par *, struct reg_par *, struct output *, unsigned int, unsigned int, unsigned int, double);
}

static inline double get_quantile(int);
static void get_slot_counts(int, double *);
static void initialize_bins(void);
static void fill_bins(int, double *);
static int compare(const void *, const void *);
static void sort_bins(void);
static void compute_quantiles(int, double, struct write *);
double quantile(double, int, double *, struct write *);
#endif
