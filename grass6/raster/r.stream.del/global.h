#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>


					/* define */
	
#define SPRING struct sprs
SPRING { 
    int r, c;
    int val;
};	

					/* functions.c */ 

/* io.c */
int create_maps(void);
int max_link(void);
int write_map(void);
int set_null(void);

/* delete */
int find_springs(int max_link);
int delete_join(int springs_num);

				/* variables */

#ifdef MAIN
#	define GLOBAL
#else
#	define GLOBAL extern
#endif

GLOBAL struct Cell_head window;
GLOBAL char *in_dirs, *in_streams;	/* input dirrection and accumulation raster names*/
GLOBAL char *out_streams;
GLOBAL int zeros; /* flags */
GLOBAL int threshold;

GLOBAL CELL **dirs, **streams; /* matrix with input data streams is used as output data*/

GLOBAL int nrows, ncols; 

GLOBAL SPRING *springs;

GLOBAL struct History history;	/* holds meta-data (title, comments,..) */





