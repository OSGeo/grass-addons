#ifndef _GLOBAL_H_
#define _GLOBAL_H_

#ifdef _MSC_VER
#include <winsock2.h>
/* gettimeofday.c */
int gettimeofday(struct timeval *, struct timezone *);
#else
#include <sys/time.h>
#endif
#include <grass/raster.h>

#define E             1
#define SE            2
#define S             4
#define SW            8
#define W             16
#define NW            32
#define N             64
#define NE            128

#define DIR(row, col) dir_map->cells[(size_t)(row)*ncols + (col)]

struct raster_map {
    int nrows, ncols;
    CELL *cells;
};

/* timeval_diff.c */
long long timeval_diff(struct timeval *, struct timeval *, struct timeval *);

/* accumulate.c */
void accumulate(struct raster_map *, struct raster_map *);

#endif
