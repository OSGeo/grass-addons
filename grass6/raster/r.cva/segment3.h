#ifndef __SEGMENT3_H__
#define __SEGMENT3_H__

struct point *segment(int segment_no, int xmax, int ymax,
		      double slope_1, double slope_2, 
		      int flip, int sign_on_y, int sign_on_x,
		      double viewpt_elev, 
		      SEGMENT *seg_in_p, SEGMENT *seg_out_p, SEGMENT *seg_patt_p, 
		      int row_viewpt, int col_viewpt, int patt_flag,
		      CELL cell_no, RASTER_MAP_TYPE data_type);

#endif
