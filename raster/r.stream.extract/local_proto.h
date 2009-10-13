
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

struct ast_point
{
    int idx;
    char asp;
};

struct point
{
    int r, c;
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
} *stream_node;

int nrows, ncols;
struct ast_point *astar_pts;
unsigned int n_search_points, n_points, nxt_avail_pt;
unsigned int heap_size, *astar_added;
unsigned int n_stream_nodes, n_alloc_nodes;
struct point *outlets;
unsigned int n_outlets, n_alloc_outlets;
DCELL *acc, *accweight;
CELL *ele;
CELL *stream;
int *strahler, *horton;   /* strahler and horton order */
FLAG *worked, *in_list;
extern char drain[3][3];
unsigned int first_cum;
char sides;
int c_fac;
int ele_scale;
struct RB_TREE *draintree;

/* load.c */
int load_maps(int, int, int);

/* do_astar.c */
int do_astar(void);
unsigned int heap_add(int, int, CELL, char);

/* streams.c */
int do_accum(double);
int extract_streams(double, double, int, int);

/* thin.c */
int thin_streams(void);

/* del_streams.c */
int del_streams(int);
int seg_length(int, unsigned int *);
int del_stream_seg(int);
int update_stream_id(int, int);

/* close.c */
int close_maps(char *, char *, char *);

#endif /* __LOCAL_PROTO_H__ */
