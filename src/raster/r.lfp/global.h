#ifndef _GLOBAL_H_
#define _GLOBAL_H_

#include <stdint.h>

#ifdef _MSC_VER
#include <winsock2.h>
/* gettimeofday.c */
int gettimeofday(struct timeval *, struct timezone *);
#else
#include <sys/time.h>
#endif

#define USE_LESS_MEMORY
#define LOOP_THEN_TASK

#define REALLOC_INCREMENT 1024

#define NE                128
#define N                 64
#define NW                32
#define W                 16
#define SW                8
#define S                 4
#define SE                2
#define E                 1

struct raster_map {
    int nrows, ncols;
    union {
        void *v;
        unsigned char *byte;
    } cells;
};

struct outlet_list {
    int nalloc, n;
    int *row, *col;
    int *id;
    int *northo, *ndia;
    double *lflen;
    struct point_list *head_pl;
    /* for full lfp */
    char *has_up;
    int *down;
    double *flen;
};

struct point_list {
    int nalloc, n;
    int *row, *col;
    double *x, *y;
};

#ifdef LOOP_THEN_TASK
#ifdef _MAIN_C_
#define GLOBAL
#else
#define GLOBAL extern
#endif

GLOBAL int tracing_stack_size;
#endif

/* timeval_diff.c */
long long timeval_diff(struct timeval *, struct timeval *, struct timeval *);

/* direction.c */
struct raster_map *read_direction(char *, char *, char *);
void free_raster_map(struct raster_map *);

/* outlets.c */
struct outlet_list *read_outlets(char *, char *, char *, struct raster_map *,
                                 int);

/* outlet_list.c */
void init_outlet_list(struct outlet_list *);
void reset_outlet_list(struct outlet_list *);
void free_outlet_list(struct outlet_list *);
void add_outlet(struct outlet_list *, int, int, int, int);

/* point_list.c */
void init_point_list(struct point_list *);
void reset_point_list(struct point_list *);
void free_point_list(struct point_list *);
void add_point(struct point_list *, int, int);
void add_point_xy(struct point_list *, double, double);

/* lfp_lessmem.c */
void lfp_lessmem(struct raster_map *, struct outlet_list *, int, int);

/* write.c */
void write_lfp(const char *, const char *, struct outlet_list *,
               struct raster_map *);
void write_head_points(const char *, const char *, struct outlet_list *);
void write_head_coors(const char *, const char *, struct outlet_list *);

#endif
