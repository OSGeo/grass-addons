#ifndef __LINE_OF_SIGHT_H__
#define __LINE_OF_SIGHT_H__

#include <grass/gis.h>
#include <grass/segment.h>

void line_of_sight (CELL cell_no, int row_viewpt, int col_viewpt,
		    int nrows, int ncols, double viewpt_elev,
		    struct point *heads[],
            SEGMENT *seg_in_p, SEGMENT *seg_out_1_p, SEGMENT *seg_patt_p,
		    int patt_flag, RASTER_MAP_TYPE data_type);

#endif
