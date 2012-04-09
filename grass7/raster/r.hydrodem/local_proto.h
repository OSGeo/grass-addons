
#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/gis.h>
#include <grass/raster.h>
#include "seg.h"
#include "flag.h"

#define INDEX(r, c) ((r) * ncols + (c))
#define MAXDEPTH 1000     /* maximum supported tree depth of stream network */

struct ddir
{
    int pos;
    int dir;
};

struct point
{
    int r, c;
};

struct heap_point {
   unsigned int added;
   CELL ele;
   int r, c;
};

struct sink_list
{
    int r, c;
    struct sink_list *next;
};

struct snode
{
    int r, c;
    int id;
    int n_trib;           /* number of tributaries */
    int n_trib_total;     /* number of all upstream stream segments */
    int n_alloc;          /* n allocated tributaries */
    int *trib;
    double *acc;
};

extern struct snode *stream_node;
extern int nrows, ncols;
extern unsigned int n_search_points, n_points, nxt_avail_pt;
extern unsigned int heap_size;
extern unsigned int n_sinks;
extern int n_mod_max, size_max;
extern int do_all, keep_nat, nat_thresh;
extern unsigned int n_stream_nodes, n_alloc_nodes;
extern struct point *outlets;
extern struct sink_list *sinks, *first_sink;
extern unsigned int n_outlets, n_alloc_outlets;
extern char drain[3][3];
extern unsigned int first_cum;
extern char sides;
extern int c_fac;
extern int ele_scale;
extern struct RB_TREE *draintree;

extern SSEG search_heap;
extern SSEG astar_pts;
extern BSEG bitflags;
extern CSEG ele;
extern BSEG draindir;
extern CSEG stream;

/* load.c */
int load_map(int, int);

/* init_search.c */
int init_search(int);

/* do_astar.c */
int do_astar(void);
unsigned int heap_add(int, int, CELL, char, char);

/* hydro_con.c */
int hydro_con(void);
int one_cell_extrema(int, int, int);

/* close.c */
int close_map(char *, int);

#endif /* __LOCAL_PROTO_H__ */
