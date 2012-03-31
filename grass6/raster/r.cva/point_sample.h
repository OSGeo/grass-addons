#ifndef __POINT_SAMPLE_H__
#define __POINT_SAMPLE_H__

#include <grass/gis.h>
#include <grass/segment.h>

void point_sample (struct Cell_head *window, int nrows, int ncols,
		   SEGMENT *seg_in_p, SEGMENT *seg_out_1_p,
		   SEGMENT *seg_out_2_p, SEGMENT *seg_patt_p,
		   SEGMENT *seg_patt_p_v,
		   double *attempted_sample, double *actual_sample,
		   char *site_file, int terse, RASTER_MAP_TYPE data_type,
		   int ignore_att);

#endif
