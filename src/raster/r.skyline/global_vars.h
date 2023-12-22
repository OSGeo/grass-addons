/***********************************************************************/
/*
   global_vars.h

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

   NOTES
   #define DEBUG in this file to enable debug functions in sort.c
   list.c

 */

/***********************************************************************/

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#define NO_SKYLINE     999.0
#define VIEWPT_SKYLINE 1000.0

GLOBAL RASTER_MAP_TYPE viewshed_buf_cell_type;
GLOBAL RASTER_MAP_TYPE dem_buf_cell_type;
GLOBAL RASTER_MAP_TYPE hoz_az_buf_cell_type;
GLOBAL RASTER_MAP_TYPE hoz_inc_buf_cell_type;
GLOBAL RASTER_MAP_TYPE hoz_type_buf_cell_type;
GLOBAL RASTER_MAP_TYPE edges_buf_cell_type;
GLOBAL RASTER_MAP_TYPE skyline_buf_cell_type;
GLOBAL int viewpt_row, viewpt_col;
GLOBAL double max_dist;
GLOBAL int do_skyline;
GLOBAL int do_hoz_az;
GLOBAL int do_hoz_inc;
GLOBAL int do_hoz_type;
GLOBAL int do_edges;
GLOBAL int do_profile;
GLOBAL int e_col;
GLOBAL int w_col;
GLOBAL int n_row;
GLOBAL int s_row;
GLOBAL struct Cell_head window; /* Region info used for sites
                                   option */
