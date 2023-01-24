#ifndef R_PI_H
#define R_PI_H

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/stats.h>

#define TYPE_NOTHING -1
#define TYPE_NOGO    -2

/* TODO: we need to talk about these definitions... */
#define MIN_DOUBLE   -1000000
#define MAX_DOUBLE   1000000.0
#define MAX_INT      0x7FFFFFFF
#define RESOLUTION   10000

typedef struct {
    int x, y;
} Position;

typedef struct {
    int x, y;
    int neighbors;
    double value;
} Coords;

/* draw.c */
void draw_line(int *map, int val, int x1, int y1, int x2, int y2, int sx,
               int sy, int width);

/* frag.c */
Coords *writeFrag(int *flagbuf, Coords *actpos, int row, int col, int nrows,
                  int ncols, int nbr_cnt);
int writeFragments(Coords **fragments, int *flagbuf, int nrows, int ncols,
                   int nbr_cnt);

/* helpers.c */
int Round(double d);
int Random(int max);
double Randomf();
void print_buffer(int *buffer, int sx, int sy);
void print_d_buffer(DCELL *buffer, int sx, int sy);
void print_map(double *map, int size);
void print_array(DCELL *buffer, int size);
void print_int_array(char *title, int *buffer, int size);
void print_fragments(Coords **, int);

/* stat_method.c */
DCELL average(DCELL *vals, int count);
DCELL variance(DCELL *vals, int count);
DCELL std_deviat(DCELL *vals, int count);
DCELL median(DCELL *vals, int count);
DCELL mode(DCELL *vals, int count);
DCELL min(DCELL *vals, int count);
DCELL max(DCELL *vals, int count);
DCELL sum(DCELL *vals, int count);
DCELL linear(DCELL value, DCELL propcost);
DCELL exponential(DCELL value, DCELL propcost);

#endif /* LOCAL_PROTO_H */
