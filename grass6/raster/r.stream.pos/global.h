#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/Vect.h>

	  /* define */

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
    int init_r, init_c;
};

	

	  /* functions.c */


/* io.c */
int open_raster(char *mapname);
int create_base_maps(void);
int stream_number(void);
int write_maps_f(char *mapname, FCELL ** map);
int write_maps_c(char *mapname, CELL ** map);
int set_null_f(FCELL ** map);
int set_null_c(CELL ** map);

/* order.c */
int trib_nums(int r, int c);
int init_streams(void);
int find_inits(void);
int calculate(void);


	  /* variables */

GLOBAL struct Cell_head window;
GLOBAL char *in_dirs, *in_streams, *out_streams, *out_streams_length;	/* input dirrection and accumulation raster names */
GLOBAL int seq_cats;
GLOBAL int multipier;
GLOBAL int stream_num;

GLOBAL CELL **dirs, **streams;	/* matrix with input data */
GLOBAL FCELL **streams_length;
GLOBAL int nrows, ncols;

GLOBAL STREAM *s_streams;	/* stream structure all parameters we have here */
GLOBAL struct History history;



