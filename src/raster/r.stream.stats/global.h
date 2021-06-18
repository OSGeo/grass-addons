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
POINT {
    int r, c;
    int is_outlet;
};
	
#define STREAM struct strs
STREAM { 
    int index;
    int is_outlet;
    int r, c; /* outlet */
    float elev_diff;
    float elev_spring, elev_outlet;
    float slope; /* cumulative */
    float gradient;
    float length; /* cumulative */
    int order;
    double basin_area; /* basin order */
    int cell_num;
};	
	
	
#define STATS struct statistics
STATS {
    int order;
    int stream_num;
    float sum_length;
    float avg_length;
    float std_length;
    float avg_slope;
    float std_slope;
    float avg_gradient;
    float std_gradient;
    double sum_area;
    double avg_area;
    double std_area;
    float avg_elev_diff;
    float std_elev_diff;
    float bifur_ratio;
    float std_bifur_ratio;
    float length_ratio;
    float std_length_ratio;
    float area_ratio;
    float std_area_ratio;
    float slope_ratio;
    float std_slope_ratio;
    float gradient_ratio;
    float std_gradient_ratio;
    float stream_frequency;
    float drainage_density;
};

					/* functions.c */ 

/* io.c */
int open_raster(char *mapname);
int create_maps(void);

/* stats */
int init_streams (void);
double fill_basin (int r,int c);
int calculate_basins (void);
int calculate_streams(void);
int stats(void);
int fifo_insert (POINT point);
POINT fifo_return_del (void);

/* print stats */
int print_stats(void);

				/* variables */

#ifdef MAIN
#	define GLOBAL
#else
#	define GLOBAL extern
#endif

GLOBAL char *in_dirs, *in_streams, *in_elev;	/* input dirrection and accumulation raster names*/
GLOBAL char *out_file;
GLOBAL int hack; /* flags */

GLOBAL double total_basins;


GLOBAL CELL **dirs, **streams; /* matrix with input data*/
GLOBAL FCELL**elevation; 
/* streams and elevation are used to store internal data during processing */

GLOBAL int nrows, ncols; 

GLOBAL POINT *fifo_outlet;
GLOBAL int tail, head;
GLOBAL int fifo_max;
	
GLOBAL int outlets_num; /* number outlets: index for stream statistics*/
GLOBAL STREAM *stat_streams;
GLOBAL STATS *ord_stats;
GLOBAL STATS stats_total;
GLOBAL int order_max;

GLOBAL struct History history;	/* holds meta-data (title, comments,..) */
GLOBAL struct Cell_head window;




