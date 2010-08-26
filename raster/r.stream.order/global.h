#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>

	  /* define */
#define NODES struct node
#define STREAMS struct stream

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



#define STREAM struct streem
STREAM {
    int stream;			/* index */
    int strahler, shreeve, horton, hack;	/* orders */
    int next_stream;
    int trib_num;
    int trib[5];	
    
    /*  int *trib; */
    double accum;
    double length;
    double stright;
    double fractal;
    double distance; /* distance to outlet */
    int topo_dim; /* topological dimension */
    /* float length; */
};

#define INITS struct init
INITS {
    int r;
    int c;
};

	  /* functions.c */

/* order.c */
int trib_nums(int r, int c);
int init_streams(int stream_num);
int find_nodes(int stream_num);
int do_cum_length (void);
int strahler(void);
int horton(void);
int shreeve(void);
int hack(void);

/* io.c */
int open_raster(char *mapname);
int create_base_maps(void);
int stream_number(void);
int open_accum(void);
int destroy_c_data(CELL ** data_name);
int destroy_d_data(DCELL ** data_name);
int write_maps(void);
int create_table (void);


	  /* variables */

GLOBAL struct Cell_head window;
GLOBAL char *in_dirs, *in_streams, *in_vector, *in_table, *in_accum;	/* input dirrection and accumulation raster names */
GLOBAL char *out_strahler, *out_shreeve, *out_hack, *out_horton, *out_topo;	/* output strahler, shreeve and class raster names */
GLOBAL int out_zero; /* zero-value background */

GLOBAL CELL **dirs, **streams;	/* matrix with input data */
GLOBAL DCELL **accum;		/* accum file is of type double */

GLOBAL int stack_max;
GLOBAL int nrows, ncols;

GLOBAL STREAM *s_streams;	/* stream structure all parameters we have here */
GLOBAL INITS *s_inits;
GLOBAL int *springs, *outlets;
GLOBAL int springs_num, outlets_num, stream_num;
