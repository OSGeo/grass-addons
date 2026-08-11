#include "globals.h"
int view_to_col(View *view, int x)
{
    return x - view->cell.left;
}

int view_to_row(View *view, int y)
{
    return y - view->cell.top;
}

int col_to_view(View *view, int col)
{
    return view->cell.left + col;
}

int row_to_view(View *view, int row)
{
    return view->cell.top + row;
}

void row_to_northing(struct Cell_head *cellhd, int row, double location,
                     double *north)
{
    *north = cellhd->north - (row + location) * cellhd->ns_res;
}

void col_to_easting(struct Cell_head *cellhd, int col, double location,
                    double *east)
{
    *east = cellhd->west + (col + location) * cellhd->ew_res;
}

void northing_to_row(struct Cell_head *cellhd, double north, int *row)
{
    *row = (cellhd->north - north) / cellhd->ns_res;
}

void easting_to_col(struct Cell_head *cellhd, double east, int *col)
{
    *col = (east - cellhd->west) / cellhd->ew_res;
}

void from_screen_to_geo(View *view, int x, int y, double *east, double *north)
{
    int row, col;

    col = view_to_col(view, x);
    col_to_easting(&view->cell.head, col, 0.5, east);
    row = view_to_row(view, y);
    row_to_northing(&view->cell.head, row, 0.5, north);
}
