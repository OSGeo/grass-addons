#ifndef __PTS_ELIM3_H__
#define __PTS_ELIM3_H__

int NULLPT = 999999.999999;

struct point *hidden_point_elimination (struct point *head,
					double viewpt_elev,
					SEGMENT *seg_in_p,
					SEGMENT *seg_out_p,
					SEGMENT *seg_patt_p, 
					int quadrant, 
					int sign_on_y, int sign_on_x, 
					int row_viewpt, int col_viewpt,
					int patt_flag, CELL cell_no,
					RASTER_MAP_TYPE data_type);

#endif
