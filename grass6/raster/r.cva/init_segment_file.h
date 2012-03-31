#ifndef __INIT_SEGMENT_FILE_H__
#define __INIT_SEGMENT_FILE_H__

#include <grass/gis.h>
#include <grass/segment.h>

void init_segment_file (int nrows, int ncols, SEGMENT *seg_to_init_p, 
			SEGMENT *seg_patt_p);

#endif
