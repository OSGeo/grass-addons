#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>


					/* define */

/*define directions for code simplicity

directions according to r.watershed: MUST check all directions
|3|2|1|
|4| |8|
|5|6|7|

*/
#define SQRT2 1.414214
#define POINT struct points
#define UPSTREAM 0
#define DOWNSTREAM 1
#define RELATIVE 2

POINT {
	int r, c;
float cur_dist;
float target_elev;
	};
	
#define OUTLET struct outs
OUTLET { 
	int r, c;
	float easting;
	float northing;
	};	

					/* functions.c */ 

/* io.c */
int open_raster(char *mapname);
int create_maps(void);
void free_streams (void);
int write_distance(void);
int write_elevation(void);
int set_null_elev(void);
int set_null(FCELL **);
int write_maps(char *, FCELL **);

/* inits */
int find_chatchment_outlets(void);
int fill_catchments(OUTLET outlet);
int find_outlets(void);
int reset_distance(void);

/* distance */
int calculate_upstream(void);
int fill_maps(OUTLET outlet);
int fifo_insert (POINT point);
POINT fifo_return_del (void);


				/* variables */

#ifdef MAIN
#	define GLOBAL
#else
#	define GLOBAL extern
#endif

GLOBAL char *in_dirs, *in_streams, *in_elev;	/* input dirrection and accumulation raster names*/
GLOBAL char *out_dist, *out_elev;
GLOBAL int zeros, outs, subs, near; /* flags */
GLOBAL int method;

GLOBAL CELL **dirs, **streams; /* matrix with input data*/
GLOBAL FCELL **elevation, **distance; 
/* streams and elevation are used to store internal data during processing */

GLOBAL int nrows, ncols; 

GLOBAL POINT *fifo_outlet;
GLOBAL int tail, head;
GLOBAL int outlets_num;
GLOBAL int fifo_max;
	
GLOBAL int out; /* number of strahler and horton outlets: index */
GLOBAL OUTLET *outlets;

GLOBAL struct History history;	/* holds meta-data (title, comments,..) */
GLOBAL struct Cell_head window;




