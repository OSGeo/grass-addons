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
    RASTER_MAP_TYPE type;
    size_t cell_size;
    int nrows, ncols;
    union {
        void *v;
        CELL *int32;
        FCELL *float32;
        DCELL *float64;
    } cells;
    double null_value;
    double dx, dy;
};

/* timeval_diff.c */
long long timeval_diff(struct timeval *, struct timeval *, struct timeval *);

/* raster_io.c */
struct raster_map *read_direction(char *, char *, char *);
void nullify_raster_map(struct raster_map *);
void write_raster_map(struct raster_map *, char *);
void free_raster_map(struct raster_map *);

#endif
