#include "globals.h"
int view_to_col(view, x)
     View *view;
     int x;
{
    return x - view->cell.left;
}

int view_to_row(view, y)
     View *view;
     int y;
{
    return y - view->cell.top;
}

int col_to_view(view, col)
     View *view;
{
    return view->cell.left + col;
}

int row_to_view(view, row)
     View *view;
{
    return view->cell.top + row;
}

void row_to_northing(cellhd, row, location, north)
     struct Cell_head *cellhd;
     double location;
     double *north;
{
    *north = cellhd->north - (row + location) * cellhd->ns_res;
}

void col_to_easting(cellhd, col, location, east)
     struct Cell_head *cellhd;
     double location;
     double *east;

{
    *east = cellhd->west + (col + location) * cellhd->ew_res;
}


void northing_to_row(cellhd, north, row)
     struct Cell_head *cellhd;
     double north;
     int *row;
{
    *row = (cellhd->north - north) / cellhd->ns_res;
}

void easting_to_col(cellhd, east, col)
     struct Cell_head *cellhd;
     double east;
     int *col;
{
    *col = (east - cellhd->west) / cellhd->ew_res;
}

void from_screen_to_geo(view, x, y, east, north)
     View *view;
     int x, y;
     double *east, *north;
{
    int row, col;

    col = view_to_col(view, x);
    col_to_easting(&view->cell.head, col, 0.5, east);
    row = view_to_row(view, y);
    row_to_northing(&view->cell.head, row, 0.5, north);
}
