#ifndef _GLOBAL_H_
#define _GLOBAL_H_

#include <float.h>
#include <grass/raster.h>
#include <grass/vector.h>

#define REALLOC_INCREMENT 1024

#ifndef DBL_MAX
#define DBL_MAX 1.797693E308 /* DBL_MAX approximation */
#endif
#define OUTLET -DBL_MAX

#define NE     1
#define N      2
#define NW     3
#define W      4
#define SW     5
#define S      6
#define SE     7
#define E      8

struct cell_map {
    int nrows, ncols;
    CELL **c;
};

struct raster_map {
    RASTER_MAP_TYPE type;
    int nrows, ncols;
    union {
        void **v;
        CELL **c;
        FCELL **f;
        DCELL **d;
    } cells;
};

struct point_list {
    int nalloc, n;
    double *x, *y;
};

struct line {
    struct line_pnts *Points;
    double length;
};

struct line_list {
    int nalloc, n;
    struct line **lines;
};

#ifdef _MAIN_C_
#define GLOBAL
#else
#define GLOBAL extern
#endif

GLOBAL int dir_checks[3][3][2]
#ifdef _MAIN_C_
    = {{{SE, NW}, {S, N}, {SW, NE}},
       {{E, W}, {0, 0}, {W, E}},
       {{NE, SW}, {N, S}, {NW, SE}}}
#endif
;

/* raster.c */
void set(struct raster_map *, int, int, double);
double get(struct raster_map *, int, int);
int is_null(struct raster_map *, int, int);
void set_null(struct raster_map *, int, int);

/* point_list.c */
void init_point_list(struct point_list *);
void reset_point_list(struct point_list *);
void free_point_list(struct point_list *);
void add_point(struct point_list *, double, double);

/* line_list.c */
void init_line_list(struct line_list *);
void reset_line_list(struct line_list *);
void free_line_list(struct line_list *);
void add_line(struct line_list *, struct line *);

/* accumulate_iterative.c */
void accumulate_iterative(struct cell_map *, struct raster_map *,
                          struct raster_map *, char **, char, char);

/* accumulate_recursive.c */
void accumulate_recursive(struct cell_map *, struct raster_map *,
                          struct raster_map *, char **, char, char);

/* subaccumulate.c */
void subaccumulate(struct Map_info *, struct cell_map *, struct raster_map *,
                   struct point_list *);

/* delineate_subwatersheds_iterative.c */
void delineate_subwatersheds_iterative(struct cell_map *, char **, int *,
                                       struct point_list *);

/* delineate_subwatersheds_recursive.c */
void delineate_subwatersheds_recursive(struct cell_map *, char **, int *,
                                       struct point_list *);

/* delineate_streams.c */
void delineate_streams(struct Map_info *, struct cell_map *,
                       struct raster_map *, double, char);

/* calculate_lfp_iterative.c */
void calculate_lfp_iterative(struct Map_info *, struct cell_map *,
                             struct raster_map *, int *, char *,
                             struct point_list *);

/* calculate_lfp_recursive.c */
void calculate_lfp_recursive(struct Map_info *, struct cell_map *,
                             struct raster_map *, int *, char *,
                             struct point_list *);

#endif
