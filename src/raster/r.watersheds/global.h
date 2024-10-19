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
#include <grass/raster.h>

#define REALLOC_INCREMENT 1024

#define INDEX(row, col)   ((size_t)(row) * ncols + (col))
#define DIR(row, col)     dir_map->cells.c[INDEX(row, col)]

struct raster_map {
    RASTER_MAP_TYPE type;
    size_t cell_size;
    int nrows, ncols;
    union {
        void *v;
        unsigned char *uint8;
        CELL *c;
        FCELL *f;
        DCELL *d;
    } cells;
};

struct outlet_list {
    int nalloc, n;
    int *row, *col;
    int *id;
};

/* timeval_diff.c */
long long timeval_diff(struct timeval *, struct timeval *, struct timeval *);

/* raster_map.c */
struct raster_map *read_direction(char *, char *);
void write_watersheds(char *, struct raster_map *);
void free_raster_map(struct raster_map *);

/* outlet_list.c */
void init_outlet_list(struct outlet_list *);
void reset_outlet_list(struct outlet_list *);
void free_outlet_list(struct outlet_list *);
void add_outlet(struct outlet_list *, double, double, int);
struct outlet_list *read_outlets(char *, char *, char *);

/* delineate.c */
void delineate(struct raster_map *, struct outlet_list *, int);

/* delineate_lessmem.c */
void delineate_lessmem(struct raster_map *, struct outlet_list *);

/* delineate_moremem.c */
void delineate_moremem(struct raster_map *, struct outlet_list *);

#endif
