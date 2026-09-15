#include <grass/raster.h>
#include "globals.h"
#include "loc_func.h"

void display_one_point(View *view, double east, double north)
{
    int row, col, x, y;

    /*TODO*/ northing_to_row(&view->cell.head, north, &row); // + .5;
    easting_to_col(&view->cell.head, east, &col);            // + .5;
    y = row_to_view(view, row);
    x = col_to_view(view, col);
    dot(x, y);
}

void dot(x, y)
{
    int vx[5], vy[5];

    vx[0] = x;
    vy[0] = y - dotsize;
    vx[1] = x - dotsize;
    vy[1] = y;
    vx[2] = x;
    vy[2] = y + dotsize;
    vx[3] = x + dotsize;
    vy[3] = y;
    vx[4] = x;
    vy[4] = y - dotsize;

    R_polygon_abs(vx, vy, 5);
}

int point_in_view(view, east, north)
View *view;
double north, east;
{
    if ((north <= view->cell.head.north) && (north >= view->cell.head.south) &&
        (east <= view->cell.head.east) && (east >= view->cell.head.west))
        return 1;
    else
        return 0;
}

void rectangle(x_screen1, y_screen1, x_screen2, y_screen2)
{
    R_move_abs(x_screen1, y_screen1);
    R_cont_abs(x_screen1, y_screen2);
    R_cont_abs(x_screen2, y_screen2);
    R_cont_abs(x_screen2, y_screen1);
    R_cont_abs(x_screen1, y_screen1);
}

void point(x, y)
{
    int vx[5], vy[5];

    vx[0] = x;
    vy[0] = y - 2;
    vx[1] = x - 2;
    vy[1] = y;
    vx[2] = x;
    vy[2] = y + 2;
    vx[3] = x + 2;
    vy[3] = y;
    vx[4] = x;
    vy[4] = y - 2;

    R_polygon_abs(vx, vy, 5);
}
