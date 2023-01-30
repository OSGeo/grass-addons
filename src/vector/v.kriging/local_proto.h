#ifndef __LOCAL_PROTO__
#define __LOCAL_PROTO__

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/config.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/la.h>
#include <grass/raster3d.h>
#include <grass/glocale.h>
#include <grass/rtree.h>

#if defined(HAVE_LIBLAPACK) && defined(HAVE_LIBBLAS)
#else /* defined(HAVE_LIBBLAS) */
#warning G_matrix_product() not compiled; requires GRASS GIS compiled and installed with BLAS library support
#endif /* HAVE_BLAS && HAVE_LAPACK */

#ifndef PI
#define PI           M_PI
#define DEG2RAD(ang) (ang / 180. * PI)
#define RAD2DEG(ang) (ang / PI * 180.)
#endif

#ifndef SQUARE
#define SQUARE(a) (a * a)
#define POW3(a)   (a * a * a)
#define POW4(a)   (a * a * a * a)
#endif

struct opts {
    struct Option *input, *output, *phase, *report, *crossvalid,
        *function_var_hz, *function_var_vert, *function_var_final,
        *function_var_final_vert, *form_file, *field, *intpl, *zcol, *trend_a,
        *trend_b, *trend_c, *trend_d, *var_dir_hz, *var_dir_vert, *maxL, *maxZ,
        *nL, *nZ, *td_hz, *td_vert, *nugget_hz, *nugget_vert, *nugget_final,
        *nugget_final_vert, *sill_hz, *sill_vert, *sill_final, *sill_final_vert,
        *range_hz, *range_vert, *range_final, *range_final_vert;
};

struct flgs {
    struct Flag *d23; /* 2D/3D interpolation */
    struct Flag *bivariate;
    struct Flag *univariate;
    struct Flag *detrend;
};

struct select {
    int n;        // # of selected
    int out;      // # of the others
    int total;    // total number
    int *indices; // indices of selected
};

struct points // inputs
{
    int n;                // number of points
    double *r;            // triples of coordinates (e.g. x0 y0 z0... xn yn zn)
    struct RTree *R_tree; // spatial index
    struct RTree *Rtree_hz;   // spatial index
    struct RTree *Rtree_vert; // spatial index
    double *r_min;            // min coords
    double *r_max;            // max coords
    double max_dist;          // maximum distance
    double center[3];         // center
    double *invals;           // values to be interpolated
    struct select in_reg;     // points in region
    mat_struct *trend;
};

struct bivar {
    int vert;
    char *variogram;

    double *h;
    double max_dist;
    int nLag;
    double lag;

    int function;
    double sill;
    double nugget;
    double h_range;
};

struct parameters {
    int function; // variogram function: lin, exp, spher, Gauss, bivar
    int type;     // variogram type: hz / vert / aniso / bivar
    int const_val;
    double dir; // azimuth for variogram computing
    double td;  // maximum azimuth

    double radius;        // radius (squared maximum distance)
    double max_dist;      // maximum distance - hz / aniso
    double max_dist_vert; // maximum distance - vert

    int nLag;   // number of lags - hz / aniso
    double lag; // lag size

    int nLag_vert;   // number of lags - vert
    double lag_vert; // lag size

    double *h;    // lag distance from search point - hz / aniso
    double *vert; // lag distance from search point - vert

    int gamma_n;       // # of dissimilarities between input points
    mat_struct *gamma; // experimental variogram matrix
    double gamma_sum;  // sum of gamma values

    double nugget;
    double sill;
    double part_sill;
    double h_range;

    struct bivar horizontal; // horizontal variogram properties
    struct bivar vertical;   // vertical variogram properties

    mat_struct *A;  // plan matrix
    mat_struct *T;  // coefficients of theoretical variogram
    mat_struct *GM; // GM = theor_var(dist: input, output points)

    char *name;    // name of input vector layer
    char term[12]; // output format - gnuplot terminal
    char ext[4];   // output format - file format
};

struct var_par // parameters of experimental variogram
{
    struct parameters hz;
    struct parameters vert;
    struct parameters fin;
};

struct krig_pars // parameters of ordinary kriging
{
    int new;
    int first;
    int modified;
    mat_struct *GM;
    mat_struct *GM_Inv; // inverted GM (GM_sub) matrix
    mat_struct *rslt;
};

struct write {
    char *name; // filename
    FILE *fp;
    time_t now;
};

struct int_par // Interpolation settings
{
    int i3;  // TRUE = 3D interpolation, FALSE = 2D interpolation (user sets by
             // flag)
    char v3; // TRUE = 3D layer, FALSE = 2D layer (according to Vect_is_3d())
    int phase;
    int bivar;
    int univar;
    double aniso_ratio;
    int const_val;
    struct write *report;
    struct write *crossvalid;
};

struct reg_par // Region settings -> output extent and resolution
{
    struct Cell_head reg_2d; // region for 2D interpolation
    RASTER3D_Region reg_3d;  // region for 3D interpolation
    double west;             // region.west
    double east;             // region.east
    double north;            // region.north
    double south;            // region.south
    double bot;              // region.bottom
    double top;              // region.top
    double ew_res;           // east-west resolution
    double ns_res;           // north-south resolution
    double bt_res;           // bottom-top resolution
    int nrows;               // # of rows
    int ncols;               // # of cols
    int ndeps;               // # of deps
    int nrcd;                // # of cells
};

struct trend {
    double a;
    double b;
    double c;
    double d;
};

struct output {
    DCELL *dcell;
    int fd_2d;
    RASTER3D_Map *fd_3d;
    char *name; // name of output 2D/3D raster
    int add_trend;
    double trend[4];
};

double *get_col_values(struct Map_info *, struct int_par *, struct points *,
                       int, const char *);
void test_normality(int, double *, struct write *);
void read_points(struct Map_info *, struct reg_par *, struct points *,
                 struct int_par *, const char *, int, struct write *);
double min(double *, struct points *);
double max(double *, struct points *);

struct RTree *create_spatial_index(struct int_par *);
void insert_rectangle(int, int, struct points *);
struct ilist *find_NNs_within(int, double *, struct points *, double, double);
struct ilist *find_n_NNs(int, int, struct points *, int);
double sum_NN(int, int, struct ilist *, struct points *);

void correct_indices(int, struct ilist *, double *, struct points *,
                     struct parameters *);
int cmpVals(const void *, const void *);
void coord_diff(int, int, double *, double *);
double distance_diff(double *);
double radius_hz_diff(double *);
double zenith_angle(double *);
void triple(double, double, double, double *);
double lag_size(int, int, struct points *, struct parameters *, struct write *);
int lag_number(double, double *);
void optimize(double *, int *, double);
void variogram_restricts(struct int_par *, struct points *,
                         struct parameters *);
void geometric_anisotropy(struct int_par *, struct points *);
double find_intersect_x(double *, double *, double *, double *, struct write *);
double find_intersect_y(double *, double *, double *, double *, double,
                        struct write *);
mat_struct *LSM(mat_struct *, mat_struct *);
mat_struct *nonlin_LMS(int, double *, double *);

void E_variogram(int, struct int_par *, struct points *, struct var_par *);
void T_variogram(int, struct opts, struct parameters *, struct int_par *);
void ordinary_kriging(struct int_par *, struct reg_par *, struct points *,
                      struct var_par *, struct output *);

void LMS_variogram(struct parameters *, struct write *);
double bivar_sill(int, mat_struct *);
void sill(struct parameters *);
void sill_compare(struct int_par *, struct flgs *, struct var_par *,
                  struct points *);
int set_function(char *, struct write *);
double RBF(double *);
double linear(double, double, double);
double exponential(double, double, double, double);
double spherical(double, double, double, double);
double gaussian(double, double, double, double);
double variogram_fction(struct parameters *, double *);
void set_gnuplot(char *, struct parameters *);
void plot_experimental_variogram(struct int_par *, struct parameters *);
void plot_var(struct int_par *, int, struct parameters *);
void new_vertical(int *, int);

void variogram_type(int, char *);
void write2file_basics(struct int_par *, struct opts *);
void write2file_vector(struct int_par *, struct points *);
void write2file_values(struct write *, const char *);
void write2file_varSetsIntro(int, struct write *);
void write2file_varSets(struct write *, struct parameters *);
void write2file_variogram_E(struct int_par *, struct parameters *,
                            mat_struct *);
void write2file_variogram_T(struct write *);
void write_temporary2file(struct int_par *, struct parameters *);
void report_error(struct write *);
void read_tmp_vals(const char *, struct parameters *, struct int_par *);

void set_up_G(struct points *, struct parameters *, struct write *,
              struct krig_pars *);
mat_struct *set_up_g0(struct int_par *, struct points *, struct ilist *,
                      double *, struct parameters *);
mat_struct *submatrix(struct ilist *, mat_struct *, struct write *);
double result(struct points *, struct ilist *, mat_struct *);

double find_center(double, double);
void adjacent_cell(int, double *, struct reg_par *, double *);
void crossvalidation(struct int_par *, struct points *, struct parameters *,
                     struct reg_par *);
void cell_centre(unsigned int, unsigned int, unsigned int, struct int_par *,
                 struct reg_par *, double *, struct parameters *);
struct ilist *list_NN(struct int_par *, double *, struct points *, double,
                      double);
int compare_NN(struct ilist *, struct ilist *, int);
void make_subsamples(struct int_par *, struct ilist *, double *, int, int,
                     struct points *, struct parameters *, struct krig_pars *);
double interpolate(struct int_par *, struct ilist *, double *, struct points *,
                   struct parameters *, struct krig_pars *);
double trend(double *, struct output *, int, struct int_par *);
int new_sample(struct int_par *, struct ilist *, struct ilist *,
               struct points *, int, int, int, double *, double, double,
               struct reg_par *, struct parameters *, struct krig_pars *,
               int *);

void get_region_pars(struct int_par *, struct reg_par *);
void open_layer(struct int_par *, struct reg_par *, struct output *);
void write2layer(struct int_par *, struct reg_par *, struct output *,
                 mat_struct *);

double get_quantile(int);
void get_slot_counts(int, double *);
void initialize_bins(void);
void fill_bins(int, double *);
int compare(const void *, const void *);
void sort_bins(void);
void compute_quantiles(int, double *, struct write *);
double quantile(double, int, double *, struct write *);
#endif
