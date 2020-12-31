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

#define IS_POINT -999
#define N_AXIAL_COUNT_CATS 13
#define NPOS22_5 0
#define NPOS45   1
#define NPOS67_5 2
#define NPOS90   3
#define NPOS     4
#define SUMPOS   5
#define NNEG22_5 6
#define NNEG45   7
#define NNEG67_5 8
#define NNEG90   9
#define NNEG     10
#define SUMNEG   11
#define NZERO    12

GLOBAL RASTER_MAP_TYPE input_buf_cell_type;
GLOBAL RASTER_MAP_TYPE output_buf_cell_type;
GLOBAL RASTER_MAP_TYPE segment_buf_cell_type;
GLOBAL int do_bearing, do_distance, do_relative_bearing;
GLOBAL int do_segments, do_square_segments, do_eight_segments;
GLOBAL double east, north;
GLOBAL int point_row, point_col;
GLOBAL int do_hoz_az;
GLOBAL int e_col;
GLOBAL int w_col;
GLOBAL int n_row;
GLOBAL int s_row;
GLOBAL struct Cell_head window;   /* Region info used for sites 
				     option */

