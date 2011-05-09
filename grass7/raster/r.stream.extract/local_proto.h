
#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/raster.h>
#include "flag.h"
#include "seg.h"

#define INDEX(r, c) ((r) * ncols + (c))
#define MAXDEPTH 1000     /* maximum supported tree depth of stream network */

#define POINT       struct a_point
POINT {
    int r, c;
};

#define HEAP_PNT    struct heap_point
HEAP_PNT {
   unsigned int added;
   CELL ele;
   POINT pnt;
};

#define WAT_ALT    struct wat_altitude
WAT_ALT {
   CELL ele;
   DCELL wat;
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
} *stream_node;

GLOBAL int nrows, ncols;
GLOBAL unsigned int n_search_points, n_points, nxt_avail_pt;
GLOBAL unsigned int heap_size;
GLOBAL unsigned int n_stream_nodes, n_alloc_nodes;
GLOBAL POINT *outlets;
GLOBAL unsigned int n_outlets, n_alloc_outlets;
GLOBAL char drain[3][3];
GLOBAL char sides;
GLOBAL int c_fac;
GLOBAL int ele_scale;
GLOBAL int have_depressions;

GLOBAL SSEG search_heap;
GLOBAL SSEG astar_pts;
GLOBAL BSEG bitflags;
GLOBAL SSEG watalt;
GLOBAL BSEG asp;
GLOBAL CSEG stream;

/* load.c */
int load_maps(int, int);

/* init_search.c */
int init_search(int);

/* do_astar.c */
int do_astar(void);
unsigned int heap_add(int, int, CELL);

/* streams.c */
int do_accum(double);
int extract_streams(double, double, int, int);

/* thin.c */
int thin_streams(void);

/* basins.c */
int basin_borders(void);

/* del_streams.c */
int del_streams(int);

/* close.c */
int close_maps(char *, char *, char *);

#endif /* __LOCAL_PROTO_H__ */
