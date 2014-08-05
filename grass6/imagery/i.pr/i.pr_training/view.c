#include <string.h>
#include <grass/raster.h>
#include "globals.h"
#include "loc_func.h"

void Configure_view(view, name, mapset, ns_res, ew_res)
     View *view;
     char *name, *mapset;
     double ns_res, ew_res;	/* original map resolution */
{
    Erase_view(view);
    view->cell.configured = 0;

    /* copy the cell name into the view */
    strcpy(view->cell.name, name);
    strcpy(view->cell.mapset, mapset);

    /* determine the map edges */
    view->cell.left = view->left + (view->ncols - view->cell.head.cols) / 2;
    view->cell.right = view->cell.left + view->cell.head.cols - 1;
    view->cell.top = view->top + (view->nrows - view->cell.head.rows) / 2;
    view->cell.bottom = view->cell.top + view->cell.head.rows - 1;

    /* remember original resolutions */
    view->cell.ns_res = ns_res;
    view->cell.ew_res = ew_res;

    view->cell.configured = 1;
}

int In_view(view, x, y)
     View *view;
{
    return (x >= view->left && x <= view->right && y >= view->top &&
	    y <= view->bottom);
}

void Erase_view(view)
     View *view;
{
    R_standard_color(BLACK);
    R_box_abs(view->left, view->top, view->right, view->bottom);
}

double magnification(view)
     View *view;
{
    if (!view->cell.configured)
	return ((double)0.0);
    return (view->cell.ew_res / view->cell.head.ew_res);
}
