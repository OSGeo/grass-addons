#include "globals.h"
#include "local_proto.h"

int 
Outline_cellhd (View *view, struct Cell_head *cellhd)
{
    int row,col;
    int top, bottom, left, right;

    row = northing_to_row (&view->cell.head, cellhd->north) + .5;
    top = row_to_view (view, row);

    col = easting_to_col (&view->cell.head, cellhd->west) + .5;
    left = col_to_view (view, col);

    row = northing_to_row (&view->cell.head, cellhd->south) + .5;
    bottom = row_to_view (view, row);

    col = easting_to_col (&view->cell.head, cellhd->east) + .5;
    right = col_to_view (view, col);

    Outline_box (top, bottom, left, right);

    return 0;
}
