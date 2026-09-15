#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/gis.h>
#include <grass/raster.h>

/* for grids with more than 2^31 - 1 cells */
#define GW_LARGE_INT off_t

#include "seg.h"
#include "flag.h"

#define INDEX(r, c) ((GW_LARGE_INT)(r) * ncols + (c))
#define MAXDEPTH    1000 /* maximum supported tree depth of stream network */

struct ddir {
    int pos;
    int dir;
};

struct point {
    int r, c;
};

struct heap_point {
    GW_LARGE_INT added;
    CELL ele;
    int r, c;
};

struct sink_list {
    int r, c;
    struct sink_list *next;
};

struct snode {
    int r, c;
    int id;
    int n_trib;       /* number of tributaries */
    int n_trib_total; /* number of all upstream stream segments */
    int n_alloc;      /* n allocated tributaries */
    int *trib;
    double *acc;
};

struct dir_flag {
    char dir;
    char flag;
};

extern struct snode *stream_node;
extern int nrows, ncols;
extern GW_LARGE_INT n_search_points, n_points, nxt_avail_pt;
extern GW_LARGE_INT heap_size;
extern int n_sinks;
extern int n_mod_max, size_max;
extern int do_all, force_filling, force_carving, keep_nat, nat_thresh;
extern GW_LARGE_INT n_stream_nodes, n_alloc_nodes;
extern struct point *outlets;
extern struct sink_list *sinks, *first_sink;
extern GW_LARGE_INT n_outlets, n_alloc_outlets;
extern char drain[3][3];
extern GW_LARGE_INT first_cum;
extern char sides;
extern int c_fac;
extern int ele_scale;
extern struct RB_TREE *draintree;

extern SSEG search_heap;
extern SSEG astar_pts;
extern SSEG dirflag;
/*
extern BSEG bitflags;
extern BSEG draindir;
*/
extern CSEG ele;
extern CSEG stream;

/* load.c */
int load_map(int);

/* init_search.c */
int init_search(int);

/* do_astar.c */
int do_astar(void);
GW_LARGE_INT heap_add(int, int, CELL);

/* hydro_con.c */
int hydro_con(void);
int one_cell_extrema(int, int, int);

/* close.c */
int close_map(char *, int);

#endif /* __LOCAL_PROTO_H__ */
