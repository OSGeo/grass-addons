
#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include "flag.h"
#include "rbtree.h"

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

/* global variables */
#ifdef MAIN
#       define GLOBAL
#else
#       define GLOBAL extern
#endif

GLOBAL struct snode
{
    int r, c;
    int id;
    int n_trib;           /* number of tributaries */
    int n_trib_total;     /* number of all upstream stream segments */
    int n_alloc;          /* n allocated tributaries */
    int *trib;
    double *acc;
} *stream_node;

/* global variables */
GLOBAL int nrows, ncols;
GLOBAL unsigned int *astar_pts;
GLOBAL unsigned int n_search_points, n_points, nxt_avail_pt;
GLOBAL unsigned int heap_size, *astar_added;
GLOBAL unsigned int n_stream_nodes, n_alloc_nodes;
GLOBAL struct point *outlets;
GLOBAL unsigned int n_outlets, n_alloc_outlets;
GLOBAL DCELL *acc;
GLOBAL CELL *ele;
GLOBAL char *asp;
GLOBAL CELL *stream;
GLOBAL FLAG *worked, *in_list;
GLOBAL char drain[3][3];
GLOBAL unsigned int first_cum;
GLOBAL char sides;
GLOBAL int c_fac;
GLOBAL int ele_scale;
GLOBAL int have_depressions;
GLOBAL struct RB_TREE *draintree;

/* load.c */
int load_maps(int, int, int);

/* do_astar.c */
int do_astar(void);
unsigned int heap_add(int, int, CELL, char);

/* streams.c */
int do_accum(double);
int extract_streams(double, double, int);

/* thin.c */
int thin_streams(void);

/* basins.c */
int basin_borders(void);

/* del_streams.c */
int del_streams(int);
int seg_length(int, unsigned int *);
int del_stream_seg(int);
int update_stream_id(int, int);

/* close.c */
int close_maps(char *, char *, char *);

#endif /* __LOCAL_PROTO_H__ */
