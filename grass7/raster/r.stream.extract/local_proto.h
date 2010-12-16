
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
   int added;
   CELL ele;
   POINT pnt;
};

#define WAT_ALT    struct wat_altitude
WAT_ALT {
   CELL ele;
   DCELL wat;
};

struct snode
{
    int r, c;
    int id;
    int n_trib;           /* number of tributaries */
    int n_trib_total;     /* number of all upstream stream segments */
    int n_alloc;          /* n allocated tributaries */
    int *trib;
} *stream_node;

/* global variables */
extern int nrows, ncols;
extern unsigned int n_search_points, n_points, nxt_avail_pt;
extern unsigned int heap_size;
extern unsigned int n_stream_nodes, n_alloc_nodes;
extern POINT *outlets;
extern unsigned int n_outlets, n_alloc_outlets;
extern char drain[3][3];
extern char sides;
extern int c_fac;
extern int ele_scale;
extern int have_depressions;

extern SSEG search_heap;
extern SSEG astar_pts;
extern BSEG bitflags;
extern SSEG watalt;
extern BSEG asp;
extern CSEG stream;

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
