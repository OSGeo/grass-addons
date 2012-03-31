#ifndef __CUMULATE_VISIBLE_CELLS_H__
#define __CUMULATE_VISIBLE_CELLS_H__

#include <grass/segment.h>

void cumulate_visible_cells (CELL cell_no,
                             int row_viewpt, int col_viewpt,
                             SEGMENT  *seg_out_1_p, SEGMENT  *seg_out_2_p,
                             SEGMENT *seg_patt_p,
                             struct point *heads[]);

#endif
