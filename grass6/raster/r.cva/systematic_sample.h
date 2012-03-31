#ifndef __SYSTEMATIC_SAMPLE_H__
#define __SYSTEMATIC_SAMPLE_H__

#include <grass/gis.h>
#include <grass/segment.h>

void systematic_sample (int nrows, int ncols,
			SEGMENT *seg_in_p, SEGMENT *seg_out_1_p,
			SEGMENT *seg_out_2_p, SEGMENT *seg_patt_p,
			SEGMENT *seg_patt_p_v, 
			double *attempted_sample, double *actual_sample,
			int terse,
			int absolute,
			RASTER_MAP_TYPE data_type);


#endif
