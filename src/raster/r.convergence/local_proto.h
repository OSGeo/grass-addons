#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/glocale.h>
#include <grass/gis.h>
#include <grass/raster.h>

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

/*
   PI2= PI/2
   PI4= PI/4
   M2PI=2*PI
 */
#ifndef PI2
#define PI2 (2 * atan(1))
#endif

#ifndef PI4
#define PI4 (atan(1))
#endif

#ifndef PI
#define PI (4 * atan(1))
#endif

#ifndef M2PI
#define M2PI (8 * atan(1))
#endif

#ifndef PI2PERCENT
#define PI2PERCENT (50 / atan(1))
#endif

#undef MIN
#undef MAX
#define MAX(a, b)     ((a) > (b) ? (a) : (b))
#define MIN(a, b)     ((a) < (b) ? (a) : (b))
#define DEGREE2RAD(a) ((a) / (180 / PI))
#define RAD2DEGREE(a) ((a) * (180 / PI))

typedef char *STRING;
typedef enum { m_STANDARD, m_INVERSE, m_POWER, m_SQUARE, m_GENTLE } methods;

typedef struct {
    char elevname[150];
    RASTER_MAP_TYPE raster_type;
    FCELL **elev;
    int fd; /* file descriptor */
} MAPS;

typedef struct {
    double cat;
    int r, g, b
} FCOLORS;

GLOBAL int gradient, f_circular, f_slope, f_method, window_size, radius;
GLOBAL float *aspect_matrix, *distance_matrix;
GLOBAL MAPS elevation;
GLOBAL FCELL **slope;
GLOBAL FCELL **aspect;

GLOBAL int nrows, ncols;
GLOBAL double H, V;
GLOBAL struct Cell_head window;

int open_map(MAPS *rast);
int create_maps(void);
int shift_buffers(int row);
int get_cell(int col, float *buf_row, void *buf, RASTER_MAP_TYPE raster_type);
int get_slope_aspect(int row);
int get_distance(int once, int row);
int create_distance_aspect_matrix(int row);
float calculate_convergence(int row, int cur_row, int col);
int free_map(FCELL **map, int n);
