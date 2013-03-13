#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/Vect.h>

	  /* define */
#define NODES struct node
#define STREAMS struct stream
#define HACK 4
#define HORTON 2
#define STRAHLER 1
#define NONE 0

#ifndef PI
 #define PI (4*atan(1))
#endif

#define deg2rad(d) ((d)*PI/180)
#define rad2deg(r) ((r)*180/PI)



#ifdef MAIN
#  define GLOBAL
#else
#  define GLOBAL extern
#endif

/* dirs
 *** next ***

 3 | 2 | 1
 --- --- ---
 4 | 0 | 8
 --- --- --- 
 5 | 6 | 7 

 *** prev ***

 7 | 6 | 5
 --- --- ---
 8 | 0 | 4
 --- --- --- 
 1 | 2 | 3 
 */

#define STREAM struct _stream
STREAM {
    int stream;			/* index */
    int strahler, shreeve, horton, hack;	/* orders */
    int init; /* stream segment identifier (if ordering is in use) */
    int next_stream, out_stream;
    int trib_num;
    int cell_num;
    int trib[5];	
    double accum;
    int init_r, init_c;
    int out_r, out_c;
    float tangent_dir; /* tangent direction at init */
    float stream_dir;  /* final stream  direction */
};


#define DIRCELLS struct _dircells
DIRCELLS {
    int r;
    int c;
    float dir_diff;
    float small_dir_diff;
    int candidate;
    int tunning;
    int decision;
    int category;
};

#define SEGMENTS struct _segments
SEGMENTS {
    int out_stream; /* for streams == stream */
    int init_stream; /* for streams == stream */
    int cell_num;
    int seg_num;
    float dir_angle; /* final direction */
    float dir_init, dir_middle, dir_last, dir_full;
    float *angles;
    float *lengths;
    float *drops;
    int *cellnums;
    int *cats;
};

	  /* functions.c */


/* io.c */
int open_raster(char *mapname);
int create_base_maps(void);
int stream_number(void);
int close_vector(void);

/* init.c */
int trib_nums(int r, int c);
int init_streams(void);
int find_nodes(void);
int do_cum_length (void);
int cur_orders(int cur_stream, int ordering);
float calc_dir(int rp,int cp,int rn,int cn);
float calc_drop(int rp,int cp,int rn,int cn);
float calc_length(int rp,int cp,int rn,int cn);

/* order.c */
int strahler(void);
int horton(void);
int shreeve(void);
int hack(void);

/* tangent.c */
int calc_tangent(int ordering);
int add_missing_dirs(int ordering);

/* seg_line */
int do_segments(SEGMENTS *segments, int ordering);
int do_decision(SEGMENTS *segments);



	  /* variables */


GLOBAL struct Cell_head window;
GLOBAL char *in_dirs, *in_streams, *in_elev;	/* input dirrection and accumulation raster names */

GLOBAL char *out_vector;
GLOBAL char *out_table_rels;

GLOBAL struct Map_info Out;

GLOBAL int seg_length;
GLOBAL int seg_outlet;
GLOBAL float seg_treshold;
GLOBAL int radians, extended;

GLOBAL CELL **dirs, **streams;	/* matrix with input data */
GLOBAL FCELL **elevation;

GLOBAL int stack_max;
GLOBAL int nrows, ncols;
GLOBAL int ordering;

GLOBAL STREAM *s_streams;	/* stream structure all parameters we have here */
GLOBAL SEGMENTS *seg_common;

/*
GLOBAL SEGMENTS *seg_strahler;
GLOBAL SEGMENTS *seg_horton;
GLOBAL SEGMENTS *seg_hack;
*/

GLOBAL int *springs, *outlets;
GLOBAL int springs_num, outlets_num;
GLOBAL int stream_num;

GLOBAL struct line_pnts *Segments;
GLOBAL struct line_cats *Cats;






