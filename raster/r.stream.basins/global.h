#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>


/* define */

/*define directions for code simplicity

directions according to r.watershed: MUST check all directions
|3|2|1|
|4| |8|
|5|6|7|

*/

#define POINT struct points	
POINT {
    int r, c;
};
	
#define OUTLET struct outs
OUTLET { 
    int r, c;
    int val;
};	
	
/* functions.c */ 

/* io.c */
int open_raster(char *mapname);
int create_maps(void);
int max_link(void);
int write_catchment(void);
int set_null(void);
int process_coors (char **answers);
int process_cats (char **answers);
int process_vector (char *in_point);

/* cachments */
int find_outlets(void);
int reset_catchments(void);
int fill_catchments (OUTLET outlet);
int fifo_insert (POINT point);
POINT fifo_return_del (void);

				/* variables */

#ifdef MAIN
#	define GLOBAL
#else
#	define GLOBAL extern
#endif

GLOBAL struct Cell_head window;
GLOBAL char *in_dirs, *in_streams, *in_point;	/* input dirrection and accumulation raster names*/
GLOBAL char *name_catchments;
GLOBAL int zeros, cats, lasts; /* flags */

GLOBAL CELL **dirs, **streams; /* matrix with input data streams is used as output data*/

GLOBAL int nrows, ncols; 

GLOBAL POINT *fifo_outlet;
GLOBAL int outlets_num;
GLOBAL int fifo_max;
	
GLOBAL int out; /* number of strahler and horton outlets: index */
GLOBAL int *categories;

GLOBAL OUTLET *outlets;


GLOBAL struct History history;	/* holds meta-data (title, comments,..) */





