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

#define E               1
#define SE              2
#define S               4
#define SW              8
#define W               16
#define NW              32
#define N               64
#define NE              128

#define INDEX(row, col) ((size_t)(row)*ncols + (col))
#define DIR(row, col)   dir_map->cells.uint8[INDEX(row, col)]

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

/* timeval_diff.c */
long long timeval_diff(struct timeval *, struct timeval *, struct timeval *);

/* accumulate.c */
void accumulate(struct raster_map *, struct raster_map *, struct raster_map *,
                int, int, int);
void nullify_zero(struct raster_map *);

/* accumulate_c.c */
void accumulate_c(struct raster_map *, struct raster_map *);
void nullify_zero_c(struct raster_map *);

/* accumulate_co.c */
void accumulate_co(struct raster_map *, struct raster_map *);

/* accumulate_cm.c */
void accumulate_cm(struct raster_map *, struct raster_map *);

/* accumulate_cz.c */
void accumulate_cz(struct raster_map *, struct raster_map *);

/* accumulate_com.c */
void accumulate_com(struct raster_map *, struct raster_map *);

/* accumulate_coz.c */
void accumulate_coz(struct raster_map *, struct raster_map *);

/* accumulate_cmz.c */
void accumulate_cmz(struct raster_map *, struct raster_map *);

/* accumulate_comz.c */
void accumulate_comz(struct raster_map *, struct raster_map *);

/* accumulate_cw.c */
void accumulate_cw(struct raster_map *, struct raster_map *,
                   struct raster_map *);

/* accumulate_cmw.c */
void accumulate_cmw(struct raster_map *, struct raster_map *,
                    struct raster_map *);

/* accumulate_f.c */
void accumulate_f(struct raster_map *, struct raster_map *);
void nullify_zero_f(struct raster_map *);

/* accumulate_fo.c */
void accumulate_fo(struct raster_map *, struct raster_map *);

/* accumulate_fm.c */
void accumulate_fm(struct raster_map *, struct raster_map *);

/* accumulate_fz.c */
void accumulate_fz(struct raster_map *, struct raster_map *);

/* accumulate_fom.c */
void accumulate_fom(struct raster_map *, struct raster_map *);

/* accumulate_foz.c */
void accumulate_foz(struct raster_map *, struct raster_map *);

/* accumulate_fmz.c */
void accumulate_fmz(struct raster_map *, struct raster_map *);

/* accumulate_fomz.c */
void accumulate_fomz(struct raster_map *, struct raster_map *);

/* accumulate_fw.c */
void accumulate_fw(struct raster_map *, struct raster_map *,
                   struct raster_map *);

/* accumulate_fmw.c */
void accumulate_fmw(struct raster_map *, struct raster_map *,
                    struct raster_map *);

/* accumulate_d.c */
void accumulate_d(struct raster_map *, struct raster_map *);
void nullify_zero_d(struct raster_map *);

/* accumulate_do.c */
void accumulate_do(struct raster_map *, struct raster_map *);

/* accumulate_dm.c */
void accumulate_dm(struct raster_map *, struct raster_map *);

/* accumulate_dz.c */
void accumulate_dz(struct raster_map *, struct raster_map *);

/* accumulate_dom.c */
void accumulate_dom(struct raster_map *, struct raster_map *);

/* accumulate_doz.c */
void accumulate_doz(struct raster_map *, struct raster_map *);

/* accumulate_dmz.c */
void accumulate_dmz(struct raster_map *, struct raster_map *);

/* accumulate_domz.c */
void accumulate_domz(struct raster_map *, struct raster_map *);

/* accumulate_dw.c */
void accumulate_dw(struct raster_map *, struct raster_map *,
                   struct raster_map *);

/* accumulate_dmw.c */
void accumulate_dmw(struct raster_map *, struct raster_map *,
                    struct raster_map *);

#endif
