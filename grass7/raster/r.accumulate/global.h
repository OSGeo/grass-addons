#ifndef _GLOBAL_H_
#define _GLOBAL_H_

#include <grass/raster.h>
#include <grass/vector.h>

#define NE 1
#define N 2
#define NW 3
#define W 4
#define SW 5
#define S 6
#define SE 7
#define E 8

struct cell_map
{
    int rows, cols;
    CELL **c;
};

struct raster_map
{
    RASTER_MAP_TYPE type;
    int rows, cols;
    union
    {
        void **v;
        CELL **c;
        FCELL **f;
        DCELL **d;
    } map;
};

struct point_list
{
    int nalloc, n;
    double *x, *y;
};

#ifdef _MAIN_C_
#define GLOBAL
#else
#define GLOBAL extern
#endif

GLOBAL int dir_checks[3][3][2]
#ifdef _MAIN_C_
    = {
    {{SE, NW}, {S, N}, {SW, NE}},
    {{E, W}, {0, 0}, {W, E}},
    {{NE, SW}, {N, S}, {NW, SE}}
}
#endif
;

/* raster.c */
void set(struct raster_map *, int, int, double);
double get(struct raster_map *, int, int);

/* point_list.c */
void init_point_list(struct point_list *);
void reset_point_list(struct point_list *);
void free_point_list(struct point_list *);
void add_point(struct point_list *, double, double);

/* accumulate.c */
void accumulate(struct cell_map *, struct raster_map *, struct raster_map *,
                char **, char);

/* delineate_streams.c */
void delineate_streams(struct Map_info *, double, struct cell_map *,
                       struct raster_map *);

#endif
